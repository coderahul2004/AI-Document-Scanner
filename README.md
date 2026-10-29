# 📚 AI Document Scanner

A chatbot that answers questions about your own files (PDF, DOCX, XLSX, CSV, TXT).
Upload a file, click **Scan files**, and ask questions in the chat. The answer comes
from your documents, with the file name (and page/row) as the source.

I built this project to learn agentic AI with Python: RAG, tool calling and MCP.

## Features
- Upload many files at once and delete them later
- Every browser session has its own private document collection
- The AI decides by itself when to search the documents (agent with tools)
- "Tools used" box shows which tool the AI called
- Handles Gemini overload errors (retry + fallback model)

## Tech stack
Python, Streamlit, Google Gemini API, ChromaDB, LangChain (text splitter, loaders),
MCP (Model Context Protocol)

## How it works
1. **Scan:** `vector.py` reads the file, splits the text into 1000-character chunks,
   makes embeddings with Gemini and saves them in ChromaDB.
2. **Ask:** `agent.py` starts `mcp_server.py` and gives its tools
   (`search_documents`, `list_documents`) to Gemini.
3. Gemini decides which tool to call. The result goes back to Gemini in a loop (max 5 steps).
4. Gemini writes the final answer using only the tool results.

## Project structure
| File | Job |
|------|-----|
| `app.py` | Streamlit user interface |
| `agent.py` | Gemini agent loop + MCP client |
| `mcp_server.py` | MCP server with the search tools |
| `vector.py` | Read files, chunk, embed, save in ChromaDB |
| `config.py` | API key and model names |

## Run on my computer
```bash
pip install -r requirements.txt
copy .env.example .env      # then paste your Google API key inside .env
streamlit run app.py
```

## Deploy on Streamlit Cloud
1. Push the code to GitHub (`.env` is ignored by `.gitignore`)
2. Create the app on Streamlit Cloud and select `app.py`
3. App settings -> Secrets, add: `GOOGLE_API_KEY = "your_key"`

## Limitations / future improvements
- Scanned PDFs (images) are not supported yet, OCR can be added
- On Streamlit Cloud the saved files are deleted when the app restarts
- The MCP server starts again for every question; keeping it running would be faster
- Old chat sessions are not cleaned automatically