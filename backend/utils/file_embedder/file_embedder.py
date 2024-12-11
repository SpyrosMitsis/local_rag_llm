from typing_extensions import Doc
from colorama import Fore, Style
import os
from tqdm import tqdm
from spacy.lang.en import English
import pymupdf
import re
import pandas as pd
from sentence_transformers import SentenceTransformer



class FileImporter:
    def __init__(self):
        """
        Constructor for FileImporter.
        
        Parameters:
        None
        
        Returns:
        None
        
        Sets the following attributes:
        pdf_path (str): The path to the PDF file
        pages_and_texts (list[dict[str, int | float | str | list[str]]]): A list of dictionaries, each containing the page number, character count, word count, sentence count, and text for a page of the PDF
        pages_and_chunks (list[dict[str, str | int | list[str]]]): A list of dictionaries, each containing the page number, sentence chunks, and index for a page of the PDF
        embedding_model (SentenceTransformer): An instance of SentenceTransformer for generating embeddings from text
        """
        self.pdf_path: str = ""
        self.pages_and_texts: list[dict[str, int | float | str | list[str]]] = []
        self.pages_and_chunks : list[dict[str, str | int | list[str]]] = []
        self.embedding_model = SentenceTransformer(model_name_or_path="all-mpnet-base-v2",
                                     device="cuda")


    def _print_message(self, message_type: str, message: str):
        """
        Prints a message to the console with color depending on the message type.

        Parameters:
        message_type (str): The type of message to print. Can be "INFO", "ERROR", or "SUCCESS".
        message (str): The message to print.

        Returns:
        None
        """
        if message_type == "INFO":
            print(f"{Fore.YELLOW}[INFO]{Style.RESET_ALL} {message}")
        elif message_type == "ERROR":
            print(f"{Fore.RED}[ERROR]{Style.RESET_ALL} {message}")
        elif message_type == "SUCCESS":
            print(f"{Fore.GREEN}[SUCESS]{Style.RESET_ALL} {message}")
        else:
            print(f"{message}")


    def insert_pdf_file(self):
        """
        Checks and updates the PDF file path, ensuring it has the correct extension,
        and verifies its existence in the uploads directory.

        Raises:
        ValueError: If the PDF file cannot be found in the directory.

        Logs:
        Prints a success message if the file exists, or an error message if not.
        """
        if self.pdf_path[-4:] != ".pdf":
            self.pdf_path += ".pdf"

        print(self.pdf_path)

        directory = "uploads/" 
        pdf_upload_path = os.path.join(directory, self.pdf_path)

        if not os.path.exists(pdf_upload_path):
            self._print_message("ERROR", f"File:[{pdf_upload_path}] can't be found!")
            raise ValueError
        else:
            self._print_message("SUCCESS", f"The file [{self.pdf_path}] already exists")


    
    def open_and_read_pdf(self):
        """
        Opens a PDF file from the uploads directory, reads its content page by page,
        formats the text, and stores detailed information about each page.

        This method utilizes the pymupdf library to read the PDF and processes each
        page using a text formatter. The formatted text and its metrics, such as character
        count, word count, raw sentence count, and token count, are stored in the
        pages_and_texts attribute.

        Raises:
        ValueError: If the specified PDF file cannot be opened.

        Logs:
        Prints a success message upon successful processing of the PDF pages.
        """
        doc = pymupdf.open("uploads/" + self.pdf_path)
        for page_number, page in tqdm(enumerate(doc), total=len(doc), desc="Processing PDF pages"):
            text: str = page.get_text()
            formatted_text: str = self.text_formatter(text=text)
            self.pages_and_texts.append({
                    "page_number": page_number + 1,
                    "page_char_count": len(formatted_text),
                    "page_word_count": len(formatted_text.split(' ')),
                    "page_sentence_count_raw": len(formatted_text.split(". ")),
                    "page_token_count": len(formatted_text) / 4,
                    "text": formatted_text
            })
        self._print_message("SUCCESS", f"Imported {len(doc)} pages!")


    def text_formatter(self, text: str):
        """
        Cleans and formats the given text by removing newlines and trimming whitespace.

        Parameters:
        text (str): The input text to be cleaned and formatted.

        Returns:
        str: The cleaned text with newlines replaced by spaces and leading/trailing whitespace removed.
        """
        cleaned_text = text.replace('\n', ' ').strip()
        return cleaned_text


    def split_text_into_sentences(self):
    
        """
        Splits the text on each page into sentences using the Spacy library.

        This method iterates over the pages_and_texts list and uses the Spacy library to
        split the text on each page into sentences. The sentences are stored in a new key
        called "sentences" and the count of sentences is stored in a new key called
        "page_sentence_count_spacy".

        Logs:
        Prints a success message upon successful processing of the sentences.
        """
        nlp = English()
        _ = nlp.add_pipe("sentencizer")
    
        for item in tqdm(self.pages_and_texts):
            item["sentences"] = list(nlp(item['text']).sents)
    
            item['sentences'] = [str(sentence) for sentence in item["sentences"]]
            item["page_sentence_count_spacy"] = len(item["sentences"])
    
        self._print_message("SUCCESS", f"Split The document into sentences")

    
    def _split_list(self, input_list: list, slice_size: int= 10) -> list[str]:
        """
        Splits a list into smaller lists (slices) of a specified size.

        Parameters:
        input_list (list): The list to be split into smaller slices.
        slice_size (int, optional): The size of each slice. Default is 10.

        Returns:
        list[str]: A list containing the resulting slices from the input list.
        """
        return [input_list[i:i+slice_size + 1] for i in range(0, len(input_list), slice_size)]

    def chunks_from_text(self, num_sentence_chunk_size :int=10, min_token_size :int=20):
        """
        Chunks the text of each page into smaller chunks of sentences.

        Iterates over the pages_and_texts list and splits the text on each page into
        chunks of sentences. The chunks are stored in a new key called "sentence_chunks"
        and the resulting chunks are stored in the pages_and_chunks list.

        Parameters:
        num_sentence_chunk_size (int, optional): The number of sentences to be included
            in each chunk. Default is 10.
        min_token_size (int, optional): The minimum number of tokens for a chunk to be
            included in the pages_and_chunks list. Default is 20.

        Logs:
        Prints a success message upon successful processing of the chunks.
        """
        for item in tqdm(self.pages_and_texts):
            item["sentence_chunks"] = self._split_list(input_list=item["sentences"],
                                                slice_size=num_sentence_chunk_size)


        for i in tqdm(self.pages_and_texts):
            for sentence_chunk in i["sentence_chunks"]:
                chunk_dict = {}
                chunk_dict["page_number"] = i["page_number"]
                joined_sentence_chunk = "".join(sentence_chunk).replace("  ", " ").strip()
                joined_sentence_chunk = re.sub(r'\.([A-Z])', r'. \1', joined_sentence_chunk)
                chunk_dict["sentence_chunk"] = joined_sentence_chunk
                chunk_dict["chunk_char_count"] = len(joined_sentence_chunk)
                chunk_dict["chunk_word_count"] = len([word for word in joined_sentence_chunk.split(" ")])
                chunk_dict["chunk_token_count"] = len(joined_sentence_chunk) / 4
                self.pages_and_chunks.append(chunk_dict)

        self.pages_and_chunks = [chunk for chunk in self.pages_and_chunks if chunk['chunk_token_count'] > min_token_size]

        self._print_message("SUCCESS", f"Chunked the text!")


    def embed_chunks(self):
        """
        Embeds the chunks of text into vectors using the SentenceTransformer model.

        Embeds all the chunks of text in the pages_and_chunks list into vectors.
        The vectors are stored in a new key called "embedding" in the pages_and_chunks
        list.

        Parameters:
        None

        Logs:
        Prints a message upon successful embedding of the chunks.
        """
        self._print_message("INFO", "Embedding the chunks")
        for item in tqdm(self.pages_and_chunks):
            item["embedding"] = self.embedding_model.encode(sentences=item["sentence_chunk"],
                                                            batch_size=32,
                                                            convert_to_tensor=False)
        self._print_message("SUCESS", "Chunks embedded!")

    def save_pdf(self) -> bool:

        """
        Saves the embedded chunks of text to a CSV file with the same name as the original PDF file.

        The method first creates a DataFrame from the pages_and_chunks list, which contains the chunks of text
        and their corresponding embeddings. The chunks are then saved in chunks of 100 to a CSV file in the
        embeddings directory. The method returns a boolean indicating whether the file was saved successfully.

        Parameters:
        None

        Logs:
        Prints the time taken to save the chunks.
        """
        from time import perf_counter as timer

        text_chunks_and_embeddings_df = pd.DataFrame(self.pages_and_chunks)
        directory = 'embeddings/'
        os.makedirs(directory, exist_ok=True)
        pdf_save_path = os.path.join(directory, self.pdf_path + ".csv")

        chunksize = 100

        start_time = timer()
        with open(pdf_save_path, mode="w", encoding="utf-8", newline="") as file:
            # Write header for the first chunk
            text_chunks_and_embeddings_df.iloc[:0].to_csv(file, index=False)
            
            # Process data in chunks
            for chunk in tqdm(
                range(0, len(text_chunks_and_embeddings_df), chunksize), 
                desc="Saving chunks"
            ):
                text_chunks_and_embeddings_df.iloc[chunk : chunk + chunksize].to_csv(
                    file, index=False, header=False
                )

        end_time = timer()
        print(f"Saving took {end_time - start_time:.5f} seconds")

        return os.path.exists(pdf_save_path)


    def import_and_embed_pdfs(self, pdfs: list[str]|str) -> bool:

        """
        Imports a PDF file and embeds its text chunks.

        Parameters:
        pdfs (list[str]|str): The path to the PDF file(s) to be imported and embedded.

        Returns:
        bool: Whether the PDF file was successfully imported and embedded.
        """
        if isinstance(pdfs, str):
             pdfs = [pdfs]

        for i in pdfs:
            self.pdf_path = i

            self.insert_pdf_file()
            self.open_and_read_pdf()
            self.split_text_into_sentences()
            self.chunks_from_text()
            self.embed_chunks()
            return self.save_pdf()

        return False

if __name__ == "__main__":
    pdfs = ["Hands-On Machine Learning With - Aurelien Geron.pdf"
            # "Pattern Recognition and Machine - Christopher M. Bishop.pdf"
        ]

    fl = FileImporter()
    _ = fl.import_and_embed_pdfs(pdfs)
