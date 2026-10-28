import os
import traceback
import json
import asyncio
import streamlit as st
from vector import load_file, create_vectorstore, get_vectorstore, delete_document
from agent import ask
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE_DIR)
UPLOAD_DIR = "uploads"
CHAT_FILE = "last_chat.json"
os.makedirs(UPLOAD_DIR, exist_ok=True)
st.set_page_config(page_title="AI Document Scanner", page_icon="📚")
@st.cache_resource
def fresh_start():
    try:
        db = get_vectorstore()
        ids = db.get()["ids"]
        if ids:
            db.delete(ids=ids)
    except Exception as e:
        print("Could not clear vector store:", e)
    for name in os.listdir(UPLOAD_DIR):
        path = os.path.join(UPLOAD_DIR, name)
        if os.path.isfile(path):
            os.remove(path)
    return True
fresh_start()
def get_indexed_files():
    db = get_vectorstore()
    data = db.get(include=["metadatas"])
    names = set()
    for meta in data["metadatas"]:
        if meta and meta.get("source"):
            names.add(meta["source"])
    return sorted(names)
def save_and_index(uploaded_file):
    file_name = os.path.basename(uploaded_file.name)
    file_path = os.path.join(UPLOAD_DIR, file_name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    docs = load_file(file_path)
    create_vectorstore(docs)
def remove_file(file_name):
    delete_document(file_name)
    file_path = os.path.join(UPLOAD_DIR, file_name)
    if os.path.isfile(file_path):
        os.remove(file_path)
def save_chat():
    with open(CHAT_FILE, "w", encoding="utf-8") as f:
        json.dump(st.session_state.messages, f, default=str)
def load_chat():
    if os.path.isfile(CHAT_FILE):
        try:
            with open(CHAT_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []
def show_tool_calls(tool_calls):
    if tool_calls:
        with st.expander("Tools used"):
            for t in tool_calls:
                st.write("Tool:", t["name"])
                st.write("Input:", t["args"])
if "messages" not in st.session_state:
    st.session_state.messages = []
if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0
st.sidebar.title("Documents")
uploaded_files = st.sidebar.file_uploader(
    "Upload files (PDF, DOCX, XLSX, CSV, TXT)",
    type=["pdf", "docx", "xlsx", "csv", "txt"],
    accept_multiple_files=True,
    key="uploader_" + str(st.session_state.uploader_key),
)
if st.sidebar.button("Scan files"):
    if not uploaded_files:
        st.sidebar.warning("Please upload a file first.")
    else:
        results = []
        for uploaded_file in uploaded_files:
            try:
                with st.spinner("Scanning " + uploaded_file.name + "..."):
                    save_and_index(uploaded_file)
                results.append(("success", uploaded_file.name + " scanned"))
            except Exception as e:
                results.append(("error", uploaded_file.name + ": " + str(e)))
        st.session_state.scan_results = results
        st.session_state.uploader_key += 1  
        st.rerun()
for kind, text in st.session_state.pop("scan_results", []):
    if kind == "success":
        st.sidebar.success(text)
    else:
        st.sidebar.error(text)
st.sidebar.divider()
st.sidebar.subheader("Scanned files")
indexed_files = get_indexed_files()
if len(indexed_files) == 0:
    st.sidebar.write("No files yet.")
else:
    for name in indexed_files:
        col1, col2 = st.sidebar.columns([4, 1])
        col1.write(name)
        if col2.button("X", key="delete_" + name):
            remove_file(name)
            st.rerun()
st.sidebar.divider()
if os.path.isfile(CHAT_FILE):
    if st.sidebar.button("Resume last chat"):
        st.session_state.messages = load_chat()
        st.rerun()
if st.sidebar.button("Clear chat"):
    st.session_state.messages = []
    if os.path.isfile(CHAT_FILE):
        os.remove(CHAT_FILE)
    st.rerun()
st.title("📚 AI Document Scanner")
st.write("Ask questions about your uploaded documents.")
if len(indexed_files) == 0:
    st.info("Upload your files in the sidebar and click **Scan files** to start.")
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
        if msg["role"] == "assistant":
            show_tool_calls(msg.get("tool_calls", []))
question = st.chat_input("Ask something about your files...")
if question:
    history = []
    for m in st.session_state.messages:
        history.append({"role": m["role"], "content": m["content"]})
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.write(question)
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                result = asyncio.run(ask(question, history))
                answer = result["answer"]
                tool_calls = result["tool_calls"]
            except Exception as e:
                
                print("FULL AGENT ERROR:")
                traceback.print_exc()
                answer = f"Something went wrong: +{type(e).__name__}:{e}" 
                tool_calls = []
        st.write(answer)
        show_tool_calls(tool_calls)
    st.session_state.messages.append(
        {"role": "assistant", "content": answer, "tool_calls": tool_calls}
    )
    save_chat()