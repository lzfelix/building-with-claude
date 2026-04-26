from mcp.server.fastmcp import FastMCP

mcp = FastMCP("DocumentMCP", log_level="ERROR")


__docs__ = {
    "deposition.md": "This deposition covers the testimony of Angela Smith, P.E.",
    "report.pdf": "The report details the state of a 20m condenser tower.",
    "financials.docx": "These financials outline the project's budget and expenditures.",
    "outlook.pdf": "This document presents the projected future performance of the system.",
    "plan.md": "The plan outlines the steps for the project's implementation.",
    "spec.txt": "These specifications define the technical requirements for the equipment.",
}


@mcp.resource(
    uri="docs://documents",
    description="Names of all documents available for querying",
    mime_type="text/plain")
def list_docs() -> list[str]:
    return list(__docs__.keys())


@mcp.resource(
    uri="docs://documents/{doc_id}",
    description="Retrieve a single document by its id (name)",
    mime_type="text/plain")
def retrieve_document(doc_id: str) -> str:
    if doc_id not in __docs__:
        raise IndexError("Invalid document id")
    return __docs__[doc_id]


@mcp.tool(
    description="Create a new document with the given content. "
        "The document will be immediately available via docs://documents/{doc_id}.")
def create_document(doc_id: str, content: str) -> str:
    if doc_id in __docs__:
        raise ValueError(f"Document '{doc_id}' already exists")
    __docs__[doc_id] = content
    return f"Document '{doc_id}' created successfully"


if __name__ == "__main__":
    mcp.run()