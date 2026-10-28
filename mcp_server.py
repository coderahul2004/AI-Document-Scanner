from mcp.server.fastmcp import FastMCP
from vector import get_vectorstore
mcp = FastMCP("Universal RAG server")
vectorstore = get_vectorstore()
@mcp.tool()
def search_documents(question: str, file_name: str = "", k: int = 5) -> str:
    """Search uploaded PDF, DOCX, XLSX, CSV, and TXT documents.
    Args:
        question: A short, specific search query.
        file_name: Optional exact file name to search only that file.
        k: Number of chunks to return, from 1 to 10.
    """
    k = max(1, min(k, 10))
    kwargs = {"k": k}
    if file_name:
        kwargs["filter"] = {"source": file_name}
    docs = vectorstore.similarity_search(question, **kwargs)
    if not docs:
        return "No relevant content found in the uploaded documents."
    parts = []
    for index, doc in enumerate(docs, start=1):
        metadata = doc.metadata
        if "page" in metadata:
            location = f", page {int(metadata['page'])}"
        elif "row" in metadata:
            location = f", row {metadata['row']}"
        else:
            location = ""
        parts.append(
            f"[{index}] Source: {metadata.get('source', 'unknown')}"
            f"{location}\n{doc.page_content}"
        )
    return "\n\n---\n\n".join(parts)
@mcp.tool()
def list_documents() -> str:
    """List document names currently represented in the vector database."""
    data = vectorstore.get(include=["metadatas"])
    sources = sorted({
        metadata.get("source")
        for metadata in data.get("metadatas", [])
        if metadata and metadata.get("source")
    })
    if not sources:
        return "No documents have been uploaded yet."
    return "\n".join(sources)
if __name__ == "__main__":
    mcp.run()