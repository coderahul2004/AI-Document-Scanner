import os
import time
from mcp.server.fastmcp import FastMCP
from vector import get_vectorstore
mcp = FastMCP("AI Document Scanner")
collection_name = os.getenv("RAG_COLLECTION_NAME")
if not collection_name:
    raise ValueError("RAG_COLLECTION_NAME is missing.")
vectorstore = get_vectorstore(collection_name)
@mcp.tool()
def search_documents(question: str, file_name: str = "", k: int = 5) -> str:
    """Search uploaded PDF, DOCX, XLSX, CSV, and TXT documents.
    Args:
        question: A question or search query about the documents.
        file_name: Optional exact file name to search.
        k: Number of relevant chunks to return, from 1 to 10.
    """
    k = max(1, min(int(k), 10))
    search_options = {"k": k}
    if file_name:
        search_options["filter"] = {"source": file_name}
    documents = None
    error_message = ""
    for attempt in range(3):
        try:
            documents = vectorstore.similarity_search(question, **search_options)
            break
        except Exception as error:
            error_message = str(error)
            time.sleep(2 * (attempt + 1))
    if documents is None:
        return f"Search failed: {error_message}"
    if not documents:
        return "No relevant content found in the uploaded documents."
    results = []
    for index, document in enumerate(documents, start=1):
        metadata = document.metadata
        source = metadata.get("source", "unknown")
        location = ""
        if metadata.get("page") is not None:
            location = f", page {metadata['page']}"
        elif metadata.get("row") is not None:
            location = f", starting at row {metadata['row']}"
        results.append(
            f"[{index}] Source: {source}{location}\n"
            f"{document.page_content}"
        )
    return "\n\n---\n\n".join(results)
@mcp.tool()
def list_documents() -> str:
    """List document names available in the current session."""
    data = vectorstore.get(include=["metadatas"])
    file_names = sorted({
        metadata["source"]
        for metadata in data.get("metadatas", [])
        if metadata and metadata.get("source")
    })
    if not file_names:
        return "No documents have been uploaded yet."
    return "\n".join(file_names)
if __name__ == "__main__":
    mcp.run()