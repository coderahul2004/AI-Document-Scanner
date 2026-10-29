# 📚 AI Document Scanner

An AI chatbot that reads your documents and answers questions about them.
Upload PDF, DOCX, XLSX, CSV or TXT files, click **Scan files**, and ask anything in the chat.

**Live App:** https://agentic-ai-with-python-tkebkbr7j8vmgjq9oxgusf.streamlit.app/
**GitHub:** https://github.com/coderahul2004/AI-Document-Scanner

---

## 1. About the Project

Reading long documents to find one answer takes time. This project solves that problem.
The user uploads files, the app stores them in a vector database, and an AI agent searches
the documents and gives an answer with the **source file name**.

This project is built to learn **RAG (Retrieval Augmented Generation)**, **AI agents** and
**MCP (Model Context Protocol)** using Python.

---

## 2. Features

- Upload multiple files: PDF, DOCX, XLSX, CSV, TXT
- Ask questions in a chat interface
- Answers come from the uploaded documents only (no made-up facts)
- Shows the source file name (and page or row number when available)
- OCR support: scanned PDFs (images) are read using Gemini vision
- "Tools used" box shows which tool the AI called
- Delete a single file or start a **New chat** (clears all data)
- Each user gets a separate session, so documents are not mixed
- Retry and fallback model when Gemini is busy or the free limit is finished

---

## 3. Tech Stack

| Part | Technology |
|---|---|
| Language | Python |
| Frontend | Streamlit |
| AI Model | Google Gemini (gemini-2.5-flash, fallback gemini-2.5-flash-lite) |
| Embeddings | gemini-embedding-001 |
| Vector Database | ChromaDB |
| RAG helpers | LangChain (text splitter, Chroma, document loaders) |
| Agent tools | MCP (FastMCP server + MCP client) |
| File reading | pypdf, python-docx, pandas, openpyxl |

---

## 4. How It Works

```
Upload files
     ↓
Read text from file (PDF / DOCX / XLSX / CSV / TXT)
     ↓
Split text into small chunks (1000 characters, 200 overlap)
     ↓
Convert chunks to embeddings and save in ChromaDB
     ↓
User asks a question
     ↓
Agent (Gemini) calls an MCP tool
     ↓
MCP server searches ChromaDB and returns the best chunks
     ↓
Gemini writes the final answer using those chunks
```

**MCP tools:**

- `search_documents` – finds the most relevant chunks for a question
- `list_documents` – shows which files are uploaded

---

## 5. Project Structure

```
AI-Document-Scanner/
├── app.py             # Streamlit user interface
├── agent.py           # AI agent (MCP client + Gemini)
├── mcp_server.py      # MCP server with the search tools
├── vector.py          # File reading, chunking, ChromaDB functions
├── config.py          # API key and model settings
├── requirements.txt   # Python packages
├── .gitignore         # Files not uploaded to GitHub
└── README.md          # Project information
```

---

## 6. How to Run on Your Computer

**Step 1: Clone the project**

```bash
git clone https://github.com/YOUR_USERNAME/AI-Document-Scanner.git
cd AI-Document-Scanner
```

**Step 2: Create a virtual environment (recommended)**

```bash
python -m venv venv
venv\Scripts\activate
```

**Step 3: Install packages**

```bash
pip install -r requirements.txt
```

**Step 4: Add your Gemini API key**

Get a free key from [Google AI Studio](https://aistudio.google.com/apikey).
Create a file named `.env` in the project folder and write:

```
GOOGLE_API_KEY=your_api_key_here
```

**Step 5: Run the app**

```bash
streamlit run app.py
```

Open http://localhost:8501 in your browser.

---

## 7. How to Use

1. Click **Upload** in the sidebar and choose your files.
2. Click **Scan files** and wait for the success message.
3. Type your question in the chat box.
4. Click **Tools used** to see which tool the AI called.
5. Click **X** next to a file to delete it, or **New chat** to clear everything.

**Example questions**

- "Summarize this document."
- "How much money is pending in the receipt?"
- "Which files have I uploaded?"

---

## 8. Deployment (Streamlit Community Cloud)

1. Push the code to GitHub (do not upload `.env`).
2. Go to [share.streamlit.io](https://share.streamlit.io) and click **Create app**.
3. Select the repository, branch `main` and main file `app.py`.
4. In **Advanced settings**, choose Python 3.11 and add this in Secrets:

```toml
GOOGLE_API_KEY = "your_api_key_here"
```

5. Click **Deploy**.

---

## 9. Limitations

- The free Gemini API has a daily request limit, so the app can stop answering when it is finished.
- Uploaded files and the database are temporary on Streamlit Cloud (they are deleted when the app restarts).
- Only the first sheet of an Excel file is read.
- Tables inside DOCX files are not read.
- Very large CSV/XLSX files create many embeddings and can be slow.

---

## 10. Future Improvements

- Support image files (JPG, PNG) with OCR
- Read all Excel sheets and DOCX tables
- Save chat history and uploaded files permanently
- Add user login
- Show the exact page number for scanned PDFs

---

## 11. What I Learned

- How RAG works: chunking, embeddings and vector search
- How to build an AI agent that uses tools through MCP
- How to handle API errors with retry and a fallback model
- How to keep API keys safe with `.env` and Streamlit Secrets
- How to deploy a Python app using GitHub and Streamlit Cloud

---

## 12. Author

**Rahul**
Python and Agentic AI learner

- GitHub: https://github.com/YOUR_USERNAME
- LinkedIn: https://www.linkedin.com/in/YOUR_PROFILE
- Email: your_email@example.com