import os
from dotenv import load_dotenv
load_dotenv()
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
if not GOOGLE_API_KEY:
    try:
        import streamlit as st
        GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
    except Exception:
        GOOGLE_API_KEY = ""

MODEL_NAME = "gemini-2.5-flash"
FALLBACK_MODEL = "gemini-2.5-flash-lite"   
EMBEDDING_MODEL = "gemini-embedding-001"
CHROMA_DIR = os.path.join(BASE_DIR, "chroma_db")
COLLECTION_NAME = "universal_documents"