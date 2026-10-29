import os
import uuid
import shutil
import traceback
import asyncio
import streamlit as st
from vector import load_file, create_vectorstore, get_vectorstore, delete_document
from agent import ask
from config import COLLECTION_NAME, GOOGLE_API_KEY
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE_DIR)
UPLOAD_ROOT = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_ROOT, exist_ok=True)
st.set_page_config(page_title="AI Document Scanner", page_icon="📚")
if not GOOGLE_API_KEY:
    st.error("GOOGLE_API_KEY is missing. Add it in the .env file (local) or in Secrets (Streamlit Cloud).")
    st.stop()
def new_session_id():
    return uuid.uuid4().hex
if "session_id" not in st.session_state:
    st.session_state.session_id = new_session_id()
if "messages" not in st.session_state:
    st.session_state.messages = []
if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0
session_id = st.session_state.session_id
collection_name = f"{COLLECTION_NAME}_{session_id}"
upload_dir = os.path.join(UPLOAD_ROOT, session_id)
os.makedirs(upload_dir, exist_ok=True)
def get_indexed_files():
    db = get_vectorstore(collection_name)
    data = db.get(include=["metadatas"])
    names = {meta["source"] for meta in data.get("metadatas", []) if meta and meta.get("source")}
    return sorted(names)
def save_and_index(uploaded_file):
    file_name = os.path.basename(uploaded_file.name)
    file_path = os.path.join(upload_dir, file_name)
    with open(file_path, "wb") as file:
        file.write(uploaded_file.getbuffer())
    try:
        docs = load_file(file_path)
        create_vectorstore(docs, collection_name)
    except Exception:
        if os.path.isfile(file_path):
            os.remove(file_path)
        raise
def remove_file(file_name):
    delete_document(file_name, collection_name)
    file_path = os.path.join(upload_dir, file_name)
    if os.path.isfile(file_path):
        os.remove(file_path)
def show_tool_calls(tool_calls):
    if tool_calls:
        with st.expander("Tools used"):
            for tool in tool_calls:
                st.write("Tool:", tool["name"])
                st.write("Input:", tool["args"])
def get_real_error(error):
    while getattr(error, "exceptions", None):
        error = error.exceptions[0]
    return error
st.sidebar.title("Documents")
uploaded_files = st.sidebar.file_uploader(
    "Upload files (PDF, DOCX, XLSX, CSV, TXT)",
    type=["pdf", "docx", "xlsx", "csv", "txt"],
    accept_multiple_files=True,
    key=f"uploader_{st.session_state.uploader_key}"
)
if st.sidebar.button("Scan files"):
    if not uploaded_files:
        st.sidebar.warning("Please upload a file first.")
    else:
        results = []
        for uploaded_file in uploaded_files:
            try:
                with st.spinner(f"Scanning {uploaded_file.name}..."):
                    save_and_index(uploaded_file)
                results.append(("success", f"{uploaded_file.name} scanned"))
            except Exception as error:
                results.append(("error", f"{uploaded_file.name}: {error}"))
        st.session_state.scan_results = results
        st.session_state.uploader_key += 1
        st.rerun()
for kind, message in st.session_state.pop("scan_results", []):
    if kind == "success":
        st.sidebar.success(message)
    else:
        st.sidebar.error(message)
st.sidebar.divider()
st.sidebar.subheader("Scanned files")
indexed_files = get_indexed_files()
if not indexed_files:
    st.sidebar.write("No files yet.")
else:
    for name in indexed_files:
        col1, col2 = st.sidebar.columns([4, 1])
        col1.write(name)
        if col2.button("X", key=f"delete_{session_id}_{name}"):
            remove_file(name)
            st.rerun()
st.sidebar.divider()
if st.sidebar.button("New chat"):
    try:
        get_vectorstore(collection_name).delete_collection()
    except Exception as error:
        print("Could not delete old collection:", error)
    shutil.rmtree(upload_dir, ignore_errors=True)
    st.session_state.session_id = new_session_id()
    st.session_state.messages = []
    st.session_state.uploader_key += 1
    st.rerun()
st.title("📚 AI Document Scanner")
st.write("Ask questions about your uploaded documents.")
if not indexed_files:
    st.info("Upload your files in the sidebar and click **Scan files** to start.")
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])
        if message["role"] == "assistant":
            show_tool_calls(message.get("tool_calls", []))

question = st.chat_input("Ask something about your files...")
if question:
    history = [m for m in st.session_state.messages if not m.get("error")]
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.write(question)
    failed = False
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                result = asyncio.run(ask(question, history, session_id=session_id))
                answer = result["answer"]
                tool_calls = result["tool_calls"]
            except Exception as error:
                traceback.print_exception(type(error), error, error.__traceback__)
                real_error = get_real_error(error)
                answer = f"Something went wrong: {type(real_error).__name__}: {real_error}"
                tool_calls = []
                failed = True
        if failed:
            st.error(answer)
        else:
            st.write(answer)
            show_tool_calls(tool_calls)
    st.session_state.messages.append(
        {"role": "assistant", "content": answer, "tool_calls": tool_calls, "error": failed}
    )