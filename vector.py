import os
import pandas as pd
from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from docx import Document as DocxDocument
from config import (
    GOOGLE_API_KEY,
    EMBEDDING_MODEL,
    CHROMA_DIR,
    COLLECTION_NAME
)
load_dotenv()
def load_file(path):
    extension = os.path.splitext(path)[1].lower()
    file_name = os.path.basename(path)
    documents = []
    if extension == ".pdf":
        documents = PyPDFLoader(path).load()
        for page_number, document in enumerate(documents, start=1):
            document.metadata.update({
                "source": file_name,
                "file_type": "pdf",
                "page": page_number
            })
    elif extension == ".docx":
        word_file = DocxDocument(path)
        text = "\n".join(
            paragraph.text
            for paragraph in word_file.paragraphs
            if paragraph.text.strip()
        )
        if text.strip():
            documents.append(Document(
                page_content=text,
                metadata={
                    "source": file_name,
                    "file_type": "docx"
                }
            ))
    elif extension in [".xlsx", ".csv"]:
        if extension == ".xlsx":
            data = pd.read_excel(path)
        else:
            data = pd.read_csv(path)
        for index, row in data.iterrows():
            text = "\n".join(
                f"{column}: {row[column]}"
                for column in data.columns
                if pd.notna(row[column])
            )
            if text.strip():
                documents.append(Document(
                    page_content=text,
                    metadata={
                        "source": file_name,
                        "file_type": extension[1:],
                        "row": int(index) + 1
                    }
                ))
    elif extension == ".txt":
        with open(path, "r", encoding="utf-8-sig") as file:
            text = file.read()
        if text.strip():
            documents.append(Document(
                page_content=text,
                metadata={
                    "source": file_name,
                    "file_type": "txt"
                }
            ))
    else:
        raise ValueError(f"Unsupported file type: {extension}")
    if not documents:
        raise ValueError(f"No readable text found in {file_name}.")
    return documents
def get_vectorstore(collection_name=None):
    embeddings = GoogleGenerativeAIEmbeddings(
        model=EMBEDDING_MODEL,
        google_api_key=GOOGLE_API_KEY
    )
    return Chroma(
        collection_name=collection_name or COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=CHROMA_DIR
    )
def create_vectorstore(documents, collection_name=None):
    db = get_vectorstore(collection_name)
    file_names = {
        document.metadata.get("source")
        for document in documents
        if document.metadata.get("source")
    }
    for file_name in file_names:
        db.delete(where={"source": file_name})
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    chunks = splitter.split_documents(documents)
    if chunks:
        db.add_documents(chunks)
    return db
def delete_document(file_name, collection_name=None):
    db = get_vectorstore(collection_name)
    db.delete(where={"source": file_name})
    return True