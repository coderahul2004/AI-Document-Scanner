import os
import pandas as pd
from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from docx import Document as DocxDocument
from config import (GOOGLE_API_KEY,EMBEDDING_MODEL,CHROMA_DIR,COLLECTION_NAME)
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
        word_doc = DocxDocument(path)
        text = "\n".join(
            p.text for p in word_doc.paragraphs
            if p.text.strip()
        )
        if text.strip():
            docs = [Document(
                page_content=text,
                metadata={
                    "source": name,
                    "file_type": "docx"
                }
            )]
    elif ext in (".xlsx", ".csv"):
        df = (
            pd.read_excel(path)
            if ext == ".xlsx"
            else pd.read_csv(path)
        )
        for i, row in df.iterrows():
            values = [
                f"{col}: {row[col]}"
                for col in df.columns
                if pd.notna(row[col])
            ]
            if values:
                docs.append(Document(
                    page_content="\n".join(values),
                    metadata={
                        "source": name,
                        "file_type": ext[1:],
                        "row": int(i) + 1
                    }
                ))
    elif ext == ".txt":
        with open(path, "r", encoding="utf-8-sig") as f:
            text = f.read()
        if text.strip():
            docs = [Document(
                page_content=text,
                metadata={
                    "source": name,
                    "file_type": "txt"
                }
            )]
    else:
        raise ValueError(f"Unsupported file type: {ext}")
    docs = [doc for doc in docs if doc.page_content.strip()]
    if not docs:
        raise ValueError(
            f"No readable text found in {name}. "
            "The file may be empty or require OCR."
        )
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
    documents = [
        doc for doc in documents
        if doc.page_content.strip()
    ]
    if not documents:
        return db
    sources = {
        doc.metadata["source"]
        for doc in documents
        if doc.metadata.get("source")
    }
    for source in sources:
        db.delete(where={"source": source})
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        add_start_index=True
    )
    chunks = splitter.split_documents(documents)
    if chunks:
        db.add_documents(chunks)
    return db
def search_documents(query, k=4, file_name=None):
    db = get_vectorstore()
    if file_name:
        results = db.similarity_search(
            query,
            k=k,
            filter={"source": file_name}
        )
    else:
        results = db.similarity_search(query, k=k)
    return results
def delete_document(file_name):
    get_vectorstore().delete(
        where={"source": file_name}
    )
    return True