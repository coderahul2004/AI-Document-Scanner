import os
import asyncio
import streamlit as st
from vector import load_file, create_vectorstore, get_vectorstore, delete_document
from agent import ask
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE_DIR)
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)
st.set_page_config(page_title="AI Document Scanner", page_icon="📚")
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
if "messages" not in st.session_state:
    st.session_state.messages = []
st.sidebar.title("Documents")
uploaded_files = st.sidebar.file_uploader(
    "Upload files (PDF, DOCX, XLSX, CSV, TXT)",
    type=["pdf", "docx", "xlsx", "csv", "txt"],
    accept_multiple_files=True,
)
if st.sidebar.button("Index files"):
    if not uploaded_files:
        st.sidebar.warning("Please upload a file first.")
    else:
        for uploaded_file in uploaded_files:
            try:
                with st.spinner("Indexing " + uploaded_file.name + "..."):
                    save_and_index(uploaded_file)
                st.sidebar.success(uploaded_file.name + " indexed")
            except Exception as e:
                st.sidebar.error(uploaded_file.name + ": " + str(e))
st.sidebar.divider()
st.sidebar.subheader("Indexed files")
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
if st.sidebar.button("Clear chat"):
    st.session_state.messages = []
    st.rerun()
st.title("📚 AI Document Scanner")
st.write("Ask questions about your uploaded documents.")
def show_tool_calls(tool_calls):
    if tool_calls:
        with st.expander("Tools used"):
            for t in tool_calls:
                st.write("Tool:", t["name"])
                st.write("Input:", t["args"])
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
                answer = "Something went wrong: " + str(e)
                tool_calls = []
        st.write(answer)
        show_tool_calls(tool_calls)
    st.session_state.messages.append(
        {"role": "assistant", "content": answer, "tool_calls": tool_calls}
    )