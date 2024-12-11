import random
import torch
import numpy as np
import pandas as pd
import tqdm
from time import perf_counter as timer
from colorama import Fore, Style
import os

from sentence_transformers import util, SentenceTransformer



class EmbeddingsReader():
    def __init__(self):
        """
        Constructor for EmbeddingsReader.

        Sets the following attributes:
        embeddings (list): An empty list to store the embeddings from the CSV files
        device (str): The device to use for the embeddings model. If a CUDA device is
            available, it will be used, otherwise the CPU will be used.
        embedding_model (SentenceTransformer): An instance of the SentenceTransformer
            model, which is used to generate embeddings from the text.
        pages_and_chunks (list): An empty list to store the chunks of text from the PDFs
            and their corresponding embeddings.
        """
        self.embeddings = []
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.embedding_model = SentenceTransformer(model_name_or_path="all-mpnet-base-v2", 
                                      device=self.device)
        self.pages_and_chunks = []

    def _print_message(self, message_type: str, message: str):
        if message_type == "INFO":
           print(f"{Fore.YELLOW}[INFO]{Style.RESET_ALL} {message}")
        elif message_type == "ERROR":
           print(f"{Fore.RED}[ERROR]{Style.RESET_ALL} {message}")
        elif message_type == "SUCCESS":
            print(f"{Fore.GREEN}[SUCESS]{Style.RESET_ALL} {message}")
        else:
            print(f"{message}")

    def read_csvs(self, csv_file_pahts: list[str]):
        """
        Reads a list of CSV files and stores the text chunks and their corresponding embeddings in the pages_and_chunks attribute.

        The CSV files should have the following columns:
            - text (str): The text chunk
            - embedding (str): The embedding of the text chunk as a string of space-separated floats

        The embeddings are stored as a list of torch tensors in the embeddings attribute.

        Parameters:
        csv_file_pahts (list[str]): A list of paths to the CSV files to read
        """
        self.embeddings = []
        self.pages_and_chunks = []

        text_chunks_and_embedding_df = []
        if csv_file_pahts:
            for i, csv_file_path in enumerate(csv_file_pahts):
                text_chunks_and_embedding_df.append(pd.read_csv(csv_file_path))
                pdf_file_name = os.path.basename(csv_file_path).replace(".csv", "")  # Adjust based on your file naming convention
                text_chunks_and_embedding_df[i]["pdf_name"] = pdf_file_name
                text_chunks_and_embedding_df[i]["embedding"] = \
                        text_chunks_and_embedding_df[i]["embedding"].apply(lambda x: np.fromstring(x.strip("[]"), sep=" "))
                self.pages_and_chunks.append(text_chunks_and_embedding_df[i].to_dict(orient="records"))

                # Convert embeddings to torch tensor and send to device (note: NumPy arrays are float64, torch tensors are float32 by default)
                self.embeddings.append(torch.tensor(np.array(text_chunks_and_embedding_df[i]["embedding"].tolist()), dtype=torch.float32).to(self.device))

    def retrive_relevant_resources(self,
                                  query: str,
                                  n_resources_to_return: int=5,
                                  print_time: bool=True):
        """
        Retrieves the top n relevant resources based on the given query.

        Parameters:
        query (str): The query to search for
        n_resources_to_return (int): The number of relevant resources to return. Defaults to 5.
        print_time (bool): If True, prints the time taken to compute the scores. Defaults to True.

        Returns:
        A list of dictionaries, each containing the batch index, embedding index, and similarity score of the top n most relevant resources.
        """
        query_embedding = self.embedding_model.encode(query, convert_to_tensor=True)
        
        dot_scores_list = []
        index_mapping = []
        current_index = 0
        start_time = timer()
        
        # Process each batch of embeddings
        for batch_index, embedding in enumerate(self.embeddings):
            dot_scores = util.dot_score(query_embedding, embedding)[0]
            dot_scores_list.append(dot_scores)

            index_mapping.extend([(batch_index, i) for i in range(len(embedding))])
            current_index += len(embedding)
        
        total_elements = sum(len(inner_list) for inner_list in self.embeddings)
        all_scores = torch.empty((0,10))
        if total_elements:
            all_scores = torch.cat(dot_scores_list)
        
        k = min(n_resources_to_return, len(index_mapping))
        scores, indices = torch.topk(input=all_scores, k=k)
        
        end_time = timer()
        topk_results = []
        
        for score, index in zip(scores, indices):
            if index < len(index_mapping):
                batch_index, local_index = index_mapping[index]
                topk_results.append({
                    'batch': batch_index,
                    'embedding_index': local_index,
                    'similarity': score.item()
                })
        
        if print_time:
            self._print_message("INFO", f"Time taken to get scores on {total_elements} embeddings: {end_time - start_time:.5f} seconds.")
        
        return topk_results 


if __name__ == "__main__":
    er = EmbeddingsReader()
    embeddings = [
            "../../embeddings/Hands-On Machine Learning With - Aurelien Geron.pdf.csv", 
            "../../embeddings/1707.03762v7.pdf.csv",
            ]

    er.read_csvs(embeddings)

    for i in er.embeddings:
        print(i.shape)
    print(er.retrieve_relevant_resources("Ridge Regression"))
    print(er.pages_and_chunks[0][309]["sentence_chunk"], er.pages_and_chunks[0][309]["page_number"])
