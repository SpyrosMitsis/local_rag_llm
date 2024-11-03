from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline, BitsAndBytesConfig
from transformers import TextStreamer
import torch
device = 'cuda' if torch.cuda.is_available() else 'cpu'


def initialize_model(model_id: str) -> tuple[AutoModelForCausalLM, AutoTokenizer]: 
    quantization_config = BitsAndBytesConfig(load_in_4bit=True,
                                             bnb_4bit_compute_dtype=torch.float16)
    tokenizer = AutoTokenizer.from_pretrained("google/gemma-2-2b-it")
    model = AutoModelForCausalLM.from_pretrained(
            model_id,
            torch_dtype=torch.float16,
            quantization_config=quantization_config,
            low_cpu_mem_usage=True
            )

    return (model, tokenizer)

def ask():
    prompt = input("\n>")
    chat = [
            { "role": "user", "content": prompt},
            ]
    question = tokenizer.apply_chat_template(chat, tokenize=False, add_generation_prompt=True)
    question = tokenizer(question, return_tensors="pt").to(device)

    _ = model.generate(**question, streamer=streamer,
                            pad_token_id=tokenizer.eos_token_id,
                            temperature=0.1,
                            max_length=2048,
                            do_sample=True,
                            top_p=0.5,
                            repetition_penalty=1.25)



if __name__ == "__main__":

    model_id = "google/gemma-2-2b-it"
    model, tokenizer = initialize_model(model_id)
    streamer = TextStreamer(tokenizer, skip_prompt=True)

    while True:
        ask()



