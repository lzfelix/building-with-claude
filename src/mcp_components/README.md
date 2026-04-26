# MCP Components

## Structure

```
mcp_components/
├── components/
│   ├── transports.py       # async context manager that manages the stdio connection lifecycle
│   └── base_client.py      # generic MCP client with list/fetch/call_tool primitives; get_resource is abstract
├── document_server.py      # FastMCP server exposing docs as resources and a create_document tool
└── document_client.py      # implements get_resource for the docs:// URI scheme
```

`components/` contains reusable infrastructure that is not tied to any specific server. `document_server.py` and `document_client.py` are a concrete server/client pair built on top of it.

## Running the server in dev mode

Running the following scripts should be done from the project root folder.

- `mcp dev src/mcp_components/document_server.py`: Launches the server with the MCP inspector UI, useful for browsing and manually calling resources and tools:
- `uv run src/mcp_components/document_client.py`: Connects to the document server and prints all exposed capabilities (resources, resource templates, tools, prompts). The server doesn't need to be running because the client spawns its own server process.
