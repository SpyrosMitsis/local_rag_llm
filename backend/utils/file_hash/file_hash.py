from fastapi import UploadFile
import os
import shutil
from ..file_embedder.file_embedder import FileImporter
import hashlib
import csv


UPLOAD_DIRECTORY = "uploads"

if not os.path.exists(UPLOAD_DIRECTORY):
    os.makedirs(UPLOAD_DIRECTORY)


def calculate_file_hash(file: UploadFile, hash_algorithm: str="sha256") -> str:
    """
    Calculates the hash of the uploaded file using the specified hash algorithm.

    Parameters:
        file (UploadFile): The uploaded file for which the hash is to be calculated.
    hash_algorithm (str): The hash algorithm to use. Defaults to 'sha256'.

    Returns:
        str: The hexadecimal digest of the file hash.
    """
    hash_obj = hashlib.new(hash_algorithm)

    for chunk in iter(lambda: file.file.read(4096), b""):
        hash_obj.update(chunk)
    _ = file.file.seek(0)
    return hash_obj.hexdigest()


def check_file_existance(file: UploadFile, CSV_FILE_PATH: str = "file_hashes.csv") -> bool:

    """
    Checks if a file with the same hash already exists in the CSV file.

    The method first calculates the hash of the uploaded file using the specified hash algorithm.
    It then checks if an entry with the same hash exists in the CSV file. If such an entry is found,
    the method returns True, indicating that the file already exists. Otherwise, it returns False
    and adds the file's hash to the CSV file.

    Parameters:
    file (UploadFile): The uploaded file to check for existence.
    CSV_FILE_PATH (str): The path to the CSV file containing the hashes of previously uploaded files.
        Defaults to "file_hashes.csv".

    Returns:
    bool: True if a file with the same hash already exists, False otherwise.
    """
    file_hash: str = calculate_file_hash(file)
    entry_exists: bool = False

    if file.filename:
        file_name: str = file.filename


    if not os.path.exists(CSV_FILE_PATH):
        with open(CSV_FILE_PATH, mode="w", newline="", encoding="utf-8") as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(["filename", "hash"])


    with open(CSV_FILE_PATH, mode="r", newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            print(row["hash"], file_hash)
            if row["hash"] == file_hash:
                entry_exists = True
                return entry_exists

    if not entry_exists:
        with open(CSV_FILE_PATH, mode='a', newline='') as csv_file:
            writer = csv.writer(csv_file, quotechar='"', quoting=csv.QUOTE_ALL)
            writer.writerow([file_name, file_hash])
        print("Entry added.")
        return entry_exists

    


