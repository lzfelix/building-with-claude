# MCP Client Architecture

## Overview

The MCP client stack is organized into three layers, each with a distinct responsibility. Generic MCP infrastructure sits at the base, domain-specific client adapters sit in the middle, and the application layer sits on top. No layer reaches through the one below it.

![Architecture diagram](../diagrams/mcp-architecture.png)

## Layers

### Generic infrastructure (`components/`)

**`McpClientTransport`** manages the connection lifecycle. It spawns the server as a subprocess over stdio, initializes the MCP session, and exposes the session as a protected property (`_session`) accessible only to subclasses. The backing field (`__session`) is name-mangled so external callers have no path to it.

**`BaseClient`** extends `McpClientTransport` and provides all generic MCP operations: listing tools, resources, resource templates, and prompts; fetching a resource by URI (`_fetch_resource`); and calling a tool (`call_tool`). It declares `get_resource(uri)` as abstract, enforcing that every subclass defines how to interpret and return resource contents.

Nothing in `components/` knows about any specific server or URI scheme.

### Domain layer (`mcp_components/`)

**`DocumentClient`** implements `get_resource(uri)` for the `docs://` scheme. It delegates the MCP fetch to `_fetch_resource`, then owns all response parsing: picking `contents[0]`, checking the mime type, and decoding JSON if needed.

**`DocumentServer`** is the FastMCP server that `DocumentClient` connects to. It exposes:
- `docs://documents` — a static resource listing all document names
- `docs://documents/{doc_id}` — a resource template for fetching a document by id
- `create_document` — a tool for adding new documents to the collection at runtime

### Application layer (`mcp_example.py`)

**`ChatLoop`** wires the Anthropic API to one or more MCP clients. It calls only public methods on `BaseClient` — `get_resource(uri)` and `call_tool(name, args)` — with no knowledge of session internals or response shapes. It builds a cached system prompt from each client's capability metadata at session start, then exposes `read_resource` and `call_tool` as Anthropic tools so the LLM can decide what to fetch and when.

## Key design decisions

**`get_resource` takes a URI, not a logical name.** The LLM always provides a full URI when it calls `read_resource`, so accepting a URI directly is the natural public contract. Subclasses that need to construct URIs from logical names can do so internally.

**`_fetch_resource` is protected, not public.** It returns raw MCP response contents with no interpretation. Only subclasses should call it; the application layer goes through `get_resource` instead.

**`call_tool` is concrete on `BaseClient`.** MCP's tool-calling protocol is fully generic — the server defines the tool, and the session handles serialization. There is no server-specific logic to encapsulate, so no subclass needs to override it.

**The session is fully encapsulated.** `McpClientTransport.__session` is name-mangled to prevent access from outside the class. Subclasses reach it through `_session`; the application layer has no path to it at all.
