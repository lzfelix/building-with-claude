# Comments on the MCP Module

This is the module where the course skips the most content. It starts by providing a project structure and then moves to explain what tools, resources, and templated resources are. Conveniently, the course also provides the complete project, so it can be used as a reference as well.

## Capabilities and LLM Awareness

The course gives the impression that implementing capabilities (tools, resources, and templates) in the client and server is enough for the LLM to learn about them and use them as needed. At the LLM level, this is true only for tool calling: providing the tool schema is sufficient for Claude to decide when to invoke a tool. Resources and prompts are discovered automatically at startup (populating tab-completion), but the LLM is never told about them. They require explicit user action to be injected into the conversation (`@doc_id` for resources, `/command` for prompts). For more details on this topic, see [LLM Driven Discovery](./mcp-llm-driven-discovery.md).

## Scaffolding Behavior

The provided scaffolding does significant work that goes unexplained. It auto-discovers resources and prompts only for the document server built in the module. Tool discovery does extend to additional MCP servers (which can be added via CLI arguments), but resource injection (via `@`) and prompt invocation (via `/`) are hardcoded to the document server client, so those features would not work for any added server without code changes.

The user prompt is intercepted and manipulated in two ways:

1. If the user writes a word starting with `@`, the code looks up a document by that name and injects its content into the prompt.
2. If the user starts a message with `/`, the code programmatically requests that prompt from the MCP client.

When asked about this design, Claude was categorical: the approach does not scale and can be considered an anti-pattern. Step 1 in particular conflicts with letting the LLM autonomously discover and use available resources, which is one of the key benefits of MCP.

These simplifications may be acceptable in teaching material, but they should be called out as such. A production-grade application would require a more robust approach, and the course misses an opportunity to use this as a starting point for a dedicated module on the topic.

# What Was Implemented

Given these observations, after finishing the module I read the entire course code and decided to implement a solution from scratch. It can be found in [mcp_example](../src/mcp_example.py) and its corresponding [module](../src/mcp_components/). Architectural details are in the [architecture document](./mcp-architecture.md).

My version also implements eager capability discovery through system prompts. That's to say, by adding a new capability to the MCP client/server, no change must be made in the chat code for these to become usable. While useful for a toy project with only two MCP servers and potentially a handful more, I would replace this approach with a more dynamic technique at scale. Working through this led to an interesting conversation with Claude about how LLM auto-discovery through metadata can influence software architecture, and how conventional software development patterns can actually hinder LLM capabilities. More details can be found in the [MCP LLM-driven discovery](./mcp-llm-driven-discovery.md) report.

After implementing the STDIO transport, I decided to also implement an HTTP transport, which I fully delegated to Claude in [PR#7](https://github.com/lzfelix/building-with-claude/pull/7).

Unlike the course, the implementation includes two MCP modules:

- The standard document server over STDIO transport (similar to the course, though I forgot to implement prompts).
- A calendar client with the same capabilities as the [tools example](../src/tool_usage.py), but over HTTP, which the course does not cover.


# Improvement Steps

Future improvements include integrating this example with a RAG application (to be developed) and adding prompt sampling, a topic covered in the [MCP: Advanced Topics](https://anthropic.skilljar.com/model-context-protocol-advanced-topics) course. An implementation developed as part of that course is sitting on my hard drive; it is just a matter of finding time to integrate it here.
