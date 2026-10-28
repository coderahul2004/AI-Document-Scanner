
import os
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

try:
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
except (KeyError, FileNotFoundError):
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")

MODEL_NAME = "gemini-2.5-flash"
EMBEDDING_MODEL = "gemini-embedding-001"
CHROMA_DIR = "./chroma_db"
COLLECTION_NAME = "universal_documents"
