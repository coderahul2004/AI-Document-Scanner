import os
import pandas as pd
from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from docx import Document as DocxDocument
from config import GOOGLE_API_KEY, EMBEDDING_MODEL, CHROMA_DIR, COLLECTION_NAME
load_dotenv()
def load_file(path):
    ext = os.path.splitext(path)[1].lower()
    name = os.path.basename(path)
    docs = []
    if ext == ".pdf":
        docs = PyPDFLoader(path).load()
        for page_no, doc in enumerate(docs, start=1):
            doc.metadata.update({
                "source": name,
                "file_type": "pdf",
                "page": page_no
            })
    elif ext == ".docx":
        word_file = DocxDocument(path)
        text = "\n".join(
            p.text for p in word_file.paragraphs
            if p.text.strip()
        )
        if text.strip():
            docs.append(Document(
                page_content=text,
                metadata={
                    "source": name,
                    "file_type": "docx"
                }
            ))
    elif ext in [".xlsx", ".csv"]:
        if ext == ".xlsx":
            df = pd.read_excel(path)
        else:
            df = pd.read_csv(path)
        for i, row in df.iterrows():
            row_text = "\n".join(
                f"{column}: {row[column]}"
                for column in df.columns
                if pd.notna(row[column])
            )
            if row_text.strip():
                docs.append(Document(
                    page_content=row_text,
                    metadata={
                        "source": name,
                        "file_type": ext[1:],
                        "row": int(i) + 1
                    }
                ))
    elif ext == ".txt":
        with open(path, "r", encoding="utf-8-sig") as file:
            text = file.read()
        if text.strip():
            docs.append(Document(
                page_content=text,
                metadata={
                    "source": name,
                    "file_type": "txt"
                }
            ))
    else:
        raise ValueError(f"Unsupported file type: {ext}")
    if not docs:
        raise ValueError(f"No readable text found in {name}.")
    return docs
def get_vectorstore():
    embeddings = GoogleGenerativeAIEmbeddings(
        model=EMBEDDING_MODEL,
        google_api_key=GOOGLE_API_KEY
    )
    return Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=CHROMA_DIR
    )
def create_vectorstore(documents=None):
    db = get_vectorstore()
    if not documents:
        return db
    sources = {
        doc.metadata.get("source")
        for doc in documents
        if doc.metadata.get("source")
    }
    for source in sources:
        db.delete(where={"source": source})
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    chunks = splitter.split_documents(documents)
    if chunks:
        db.add_documents(chunks)
    return db
def delete_document(file_name):
    db = get_vectorstore()
    db.delete(where={"source": file_name})
    return True