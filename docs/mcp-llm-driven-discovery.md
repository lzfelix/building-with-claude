# LLM-Driven Resource Discovery in MCP

## The Conventional Approach and Its Limits

A natural first instinct when building an MCP client is to treat resource discovery as a programming problem: inspect what the server exposes, write code to enumerate it, match user queries against known resource identifiers, fetch the right content, and inject it into the prompt. This is the approach taken in Anthropic's course material, where the implementation manually lists document resources beforehand, intercepts user messages to detect mentions of specific documents, retrieves the corresponding content, and injects that content into the conversation. The LLM receives pre-fetched information rather than being given the ability to decide what it needs.

This works, but the code carries the full weight of the discovery logic. Every new resource type requires new matching code. Every new server requires understanding its structure and writing against it explicitly. The developer is doing the reasoning that the LLM could do instead.

## Treating Resources as Callable Functions

MCP exposes three kinds of things a server offers: static resources (fixed URIs), resource templates (URI patterns with variables), and tools (callable functions with typed parameters). The key insight is that these are not just data to be fetched, they are a description of a capability space. And LLMs are very good at reasoning about capability spaces when given good descriptions.

Rather than resolving resources programmatically, you can expose them to the LLM as tool calls. A single `read_resource` tool with a URI parameter gives the LLM the ability to fetch any resource it decides is relevant. A `call_tool` tool does the same for MCP tools. The LLM then operates as the decision layer: it reads the descriptions, infers relationships (like the fact that `docs://documents` returns identifiers that can be passed into `docs://documents/{doc_id}`), and calls what it needs.

This reframes the architecture. Instead of writing code that understands your server's resource structure, you write code that hands that structure to the LLM and lets it navigate.

## Upfront Disclosure and the Caching Tradeoff

For this to work, the LLM needs to know what is available. The straightforward approach is to build a system prompt at session start that lists every resource, template, and tool across all connected MCP clients, including their descriptions. This prompt is static for the duration of a session, since the server's capability surface does not change while the client is running.

Sending the same large system prompt on every conversation turn would be expensive. Anthropic's prompt caching solves this: by marking the system prompt block with `cache_control: ephemeral`, the first request pays the full ingestion cost and subsequent requests read from cache at roughly one tenth of the price. The system prompt becomes effectively free after the first turn.

The tradeoff is real though. Listing everything upfront works well when the number of resources and tools is bounded. As the capability surface grows into dozens or hundreds of items, the system prompt grows with it, and even cached tokens occupy space in the context window that could be used for conversation. At that scale, a two-stage approach makes more sense: expose a single discovery tool that the LLM can use to query what is available by topic or keyword, and only surface the relevant subset. This shifts cost from prompt size to an extra round-trip, but keeps the context clean.

For most practical MCP setups, upfront disclosure with caching is the right default. The complexity of dynamic discovery is only justified when the capability space genuinely outgrows what fits comfortably in a system prompt.

## Auto-Discovery as an Emergent Property

One consequence of this design is that resource auto-discovery is not something you implement. It is something that happens because the LLM can reason about what it has been told.

When a new resource is added to the server, it appears in the next session's system prompt automatically. The LLM reads its description, understands what it is for, and knows to use it when relevant. No code changes on the client side. No new matching logic. The server author writes a good description, and the client inherits the capability.

This is a meaningful departure from the conventional approach, where adding a new resource type to the server means auditing the client to see what needs to change. With LLM-driven discovery, the client's code is stable. The knowledge lives in the descriptions, not in the implementation.

## How This Philosophy Shapes Architecture

Adopting this approach changes what the client code is responsible for. The client no longer needs to understand the semantic structure of any particular server. It needs to understand MCP mechanics: how to list capabilities, how to fetch resources, how to call tools. That is all generic, and it belongs in a base class. Server-specific knowledge is limited to URI construction and response parsing, which belongs in server-specific subclasses.

The result is a clean separation. Generic MCP infrastructure sits in one layer. Server-specific adapters sit in another. The LLM sits above both, treating the assembled capability surface as something to reason about rather than something the code has to anticipate.

```
                        ┌─────────────────────────────┐
                        │             LLM             │  decides what to fetch and when
                        │     (decision layer)        │
                        └──────────────┬──────────────┘
                                       │ tool calls (read_resource, call_tool)
               ┌───────────────────────▼───────────────────────┐
               │          Server-specific adapters             │  URI construction,
               │     (DocumentClient, FileClient, ...)         │  response parsing
               └───────────────────────┬───────────────────────┘
                                       │ delegates to
     ┌─────────────────────────────────▼─────────────────────────────────┐
     │                   Generic MCP infrastructure                      │  session, transport,
     │             (BaseClient, transports, _fetch_resource)             │  protocol mechanics
     └────────────────────────────────────────────────────────────────────┘
```

## On Understanding LLM Mechanics as an Engineering Discipline

The difference between the two approaches described here is not primarily a technical one. The manual approach and the LLM-driven approach both work. What separates them is an understanding of what LLMs are actually good at: reading structured descriptions and making decisions based on them.

When you understand this, you stop writing code to do things the LLM can do on its own. You start writing code that gives the LLM good information and the ability to act on it. The engineering effort shifts from decision logic to interface design: how clearly can you describe a resource, a tool, a capability? How well does your system prompt communicate the structure of what is available?

This mechanical understanding shapes architecture at a deeper level than any particular pattern or framework. It determines what belongs in code and what belongs in language. Getting that boundary right is one of the more consequential decisions in building systems that include LLMs.
