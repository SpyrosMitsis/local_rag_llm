from transformers import AutoModelForCausalLM, AutoTokenizer, TextIteratorStreamer, BitsAndBytesConfig
from threading import Thread
import torch


from utils.base_prompt.base_prompt import COMPLETE_SYSTEM_PROMPT
from utils.file_reader.file_reader import EmbeddingsReader


import os
import glob


class Llm:
    def __init__(self, model_id: str = "google/gemma-2-2b-it"):
        """
        Constructor for Llm.

        Parameters:
        model_id (str): The model name or path to use for the LLM. Defaults to "google/gemma-2-2b-it".

        Returns:
        None

        Sets the following attributes:
        model_id (str): The model name or path to use for the LLM.
        torch_device (str): The device to use for the LLM. If a CUDA device is available, it will be used, otherwise the CPU will be used.
        base_directory (str): The base directory for the embeddings.
        csv_paths (list[str]): A list of paths to the CSV files containing the embeddings.
        quantization_config (BitsAndBytesConfig): The configuration for quantizing the model.
        tokenizer (AutoTokenizer): An instance of AutoTokenizer for tokenizing text.
        model (AutoModelForCausalLM): An instance of AutoModelForCausalLM for generating text.
        fr (EmbeddingsReader): An instance of EmbeddingsReader for retrieving relevant resources.
        """
        self.model_id = model_id
        self.torch_device = "cuda" if torch.cuda.is_available() else "cpu"

        self.BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.base_directory = os.path.join(self.BASE_DIR, "embeddings")
        self.csv_paths = glob.glob(os.path.join(self.base_directory, "*.csv"))

        self.quantization_config = BitsAndBytesConfig(load_in_4bit=True,
                                            bnb_4bit_compute_dtype=torch.float16)
        self.tokenizer = AutoTokenizer.from_pretrained(
                pretrained_model_name_or_path=model_id
                )

        self.model = AutoModelForCausalLM.from_pretrained(
                pretrained_model_name_or_path =model_id,
                torch_dtype=torch.float16,
                quantization_config=self.quantization_config,
                low_cpu_mem_usage=True
                )
        self.fr = EmbeddingsReader()
        self.fr.read_csvs(self.csv_paths)

        print("Running on device:", self.torch_device)
        print("CPU threads:", torch.get_num_threads())


    def prompt_formatter(self, query: str, context_items: list[dict]) -> str:
    
        """
        Format the given query and context items into a prompt that can be used as input to the instruction-tuned model.
    
        Args:
        query (str): The query string
        context_items (list[dict]): A list of dictionaries, each containing the "sentence_chunk" key with the corresponding text
    
        Returns:
        str: The formatted prompt
        """
        context_items = "- " + "\n- ".join([f"{item['sentence_chunk']} (PDF: {item['pdf_name']}) Page: {item['page_number']}" for item in context_items])
    
        
        base_prompt = COMPLETE_SYSTEM_PROMPT.format(context=context_items, query=query)
    
        #prompt template for instruction tune model
    
        dialogue_template = [
            {"role": "user",
            "content": base_prompt}
        ]
        prompt = self.tokenizer.apply_chat_template(conversation=dialogue_template,
                                               tokenize=False,
                                               add_generation_prompt=True)
        
        return prompt

    def run_generation(self, user_text: str):
    
        """
        Generates a response based on the user input text using a pre-trained causal language model.
    
        This function retrieves the top relevant context items for the given user input,
        formats them into a prompt, and generates a model response. The text generation is
        performed in a separate thread, and the output is streamed in real-time.
    
        Parameters:
        user_text (str): The input text provided by the user for which a response is generated.
    
        Returns:
        Generator[str, None, None]: A generator yielding chunks of generated text as they are produced.
        """
        new_paths = glob.glob(os.path.join(self.base_directory, "*.csv"))
        if self.csv_paths != new_paths: 
            self.csv_paths = new_paths
            self.fr.read_csvs(self.csv_paths)
    
    
        
        top_k_results = self.fr.retrive_relevant_resources(user_text)
        context_items = [self.fr.pages_and_chunks[i["batch"]][i["embedding_index"]] for i in top_k_results]
    
        prompt = self.prompt_formatter(query=user_text, context_items=context_items)
        print(prompt)


        model_inputs = self.tokenizer(prompt, return_tensors="pt").to(self.torch_device)
        streamer = TextIteratorStreamer(
                tokenizer=self.tokenizer, 
                timeout=10.0, 
                skip_prompt=True,
                skip_special_tokens=True
                )
    
        generate_kwargs = dict(
            **model_inputs,
            streamer=streamer,
            max_new_tokens=4096,
            do_sample=True,
            top_p=0.9,
            temperature=float(0.2),
            top_k=10,
            repetition_penalty=1.25
        )
    
        t = Thread(target=self.model.generate, kwargs=generate_kwargs)
        t.start()
    
        # Pull the generated text from the streamer, and update the model output.
        model_output = ""
        for new_text in streamer:
            model_output += new_text
            yield new_text
        return model_output


if __name__ == "__main__":
    llm = Llm()
    result_generator = llm.run_generation(user_text="Hello how are you?")

    for result in result_generator:
        print(result)
