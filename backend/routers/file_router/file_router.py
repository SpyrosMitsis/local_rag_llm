from fastapi import UploadFile, File, APIRouter, HTTPException
from fastapi.responses import FileResponse

import os
import shutil

from utils.file_embedder.file_embedder import FileImporter
import utils.file_hash.file_hash as fh

import csv

router = APIRouter()

PDF_DIR = os.path.abspath("uploads")
CSV_DIR = os.path.abspath("embeddings")


if not os.path.exists(PDF_DIR):
    os.makedirs(PDF_DIR)


@router.post("/uploadFiles/")
async def upload_files(files: list[UploadFile]) -> dict[str, list[str]]:

    """
    Handles the upload of PDF files, checks for duplicates, and processes new files.

    This endpoint allows the user to upload multiple PDF files. It verifies the content type 
    of each file to ensure it is a PDF. The function checks if the file already exists by comparing 
    file hashes and skips it if it does. New files are saved to the upload directory and processed 
    for text embedding.

    Parameters:
    files (list[UploadFile]): A list of UploadFile objects representing the files to be uploaded.

    Returns:
    dict[str, list[str]]: A dictionary containing lists of newly added and already added PDFs.
    """
    file_paths: list[str] = []
    newly_added_pdfs: list[str] = []
    already_added_pdfs: list[str] = []

    for file in files:
        # Check if the uploaded file is a PDF
        if file.content_type != "application/pdf":
            raise HTTPException(status_code=400, detail="Only PDF files are allowed.")

        if file.filename is not None:
            file_already_exists =  fh.check_file_existance(file)
            if file_already_exists:
                already_added_pdfs.append(file.filename)
                continue

            file_path: str = (os.path.join(PDF_DIR, file.filename))
            file_paths.append(file_path)
            if file:
                newly_added_pdfs.append(file.filename)
        
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

    if newly_added_pdfs:
        fi = FileImporter()
        _ = fi.import_and_embed_pdfs(newly_added_pdfs)

    return {
            "newly_added_pdfs": newly_added_pdfs, 
            "already_added_pdfs": already_added_pdfs, 
            }

@router.get("/pdfs")
async def list_pdfs():
    """
    Lists all PDF files currently in the uploads directory.

    Returns:
    dict[str, list[str]]: A dictionary containing a list of all PDF files in the uploads directory.
    """
    try:
        pdf_files = [f for f in os.listdir(PDF_DIR) if f.endswith('.pdf')]
        return {"pdfs": pdf_files}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pdf/{pdf_name}")
async def get_pdf(pdf_name: str):
    """
    Returns a PDF file with the given name from the uploads directory.

    Parameters:
    pdf_name (str): The name of the PDF file to retrieve.

    Returns:
    FileResponse: The PDF file.

    Raises:
    HTTPException: If the PDF file is not found in the uploads directory.
    """
    pdf_path = os.path.join(PDF_DIR, pdf_name)
    if not os.path.exists(pdf_path):
        raise HTTPException(status_code=404, detail="PDF file not found on server")
    
    return FileResponse(pdf_path, media_type='application/pdf')

@router.delete("/delete")
async def delete_pdf(pdf_name: str):
    """
    Deletes a PDF file and its associated embeddings from the server.

    The function removes the PDF file and its embeddings from the server, and also removes the entry from the CSV file that maps file names to hashes.

    Parameters:
    pdf_name (str): The name of the PDF file to delete.

    Returns:
    dict[str, str]: A dictionary containing the path of the deleted PDF file.

    Raises:
    HTTPException: If the PDF file or its embeddings are not found on the server, or if an error occurs while trying to delete the file.
    """
    pdf_path = os.path.join(PDF_DIR, pdf_name)
    csv_path = os.path.join(CSV_DIR, pdf_name + '.csv')

    if (not pdf_path.startswith(os.path.abspath(PDF_DIR))):
            #(not csv_path.startswith(os.path.abspath(CSV_DIR))):
        raise HTTPException(status_code=400, detail="Invalid file path.")

    if not os.path.isfile(pdf_path):
        raise HTTPException(status_code=404, detail="File not found.")
    elif not os.path.isfile(csv_path):
        raise HTTPException(status_code=404, detail="Embeddings not found.")

    try:

        filtered_rows = []
        with open(os.path.abspath("file_hashes.csv"), mode="r", newline='', encoding="utf-8") as file:
            reader = csv.DictReader(file)
            fieldnames = reader.fieldnames
            if not fieldnames or "filename" not in fieldnames:
                raise ValueError("The CSV file does not have the required 'filename' column.")
            
            for row in reader:
                if row["filename"] != pdf_name:
                    filtered_rows.append(row)

        for i in filtered_rows:
            print(i)
        # Write the filtered rows back to the CSV
        with open(os.path.abspath("file_hashes.csv"), mode="w", newline='', encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(filtered_rows)

            os.remove(pdf_path)
            os.remove(csv_path)

            return {"Deleted" : pdf_path}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occured: {e}")


    
