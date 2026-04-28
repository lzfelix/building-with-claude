# Comments on the MCP Module

Thus far, this is the module where the course skips most of content. At the beginning, it provides it a project structure and moves on to explain what tools, resources, and templated resources are.

In the material, the course gives the impression that by only implementing capabilities (tools, resources, and templates) in the client and the server is enough for the LLM to learn about the available resources and use them whenever necessary. At the LLM level, this is only true for tool calling: by only providing the tool schema to the LLM, it will decide by itself when to call the tool. Resources and prompts are discovered automatically at startup (populating tab-completion), but the LLM is never told about them — they require explicit user action to be injected into the conversation (`@doc_id` for resources, `/command` for prompts).

The process is considerably more manual for resources and templates. Also, capabilities discovery is not automatic and something that has to be taken care of either at LLM or implementation level. For more details on capabilities discovery, please refer to report [LLM Driven Discovery](./mcp-llm-driven-discovery.md).

Actually, the provided scaffolding does a lot of heavilifting that goes unexplained. Namely: the code will only auto-discover resources and prompts for the document server that is implemented as part of the current course module. Tool discovery does extend to additional MCP servers (which can be added via CLI arguments), but resource injection (via `@`) and prompt invocation (via `/`) are hardcoded to the document server client, so those features would not work for any other added server without code changes.

Moreover, the same scaffolding has some more interesting behavior. When asking Claude itself about the proposed solution, his answer was categoric: the approach wouldn't scale and it can be even considered an anti-pattern.

In the provided code, user prompt is intercepted and manipulated in the following ways:

1. If the user writes a word starting with `@`, some Python code will look up for a document with the name and inject that document into the user prompt.
2. If the user starts a command with `/`, the Python code will programatically ask the MCP client for that prompt.

Despite steps 1 and 2 arguably mirroring what happens in Claude Code, step #1 does't match very well with production code, especially if we want to let the LLM to auto-discover available tools and resources (which I believe is one of the most valuable points of using MCPs).

Still, it may be considered okay in the context of a teching material, but I'd expect these simplifications to be highlighted in the text and mentioning that a production-grade application would require more robust code (and, perhaps using that as a trampoline to a dedicated module or course on this direction -- Note such a course may exist, but I'm not aware of it).

# What was implemented

Given these observations, finishing the module, I read the entire code and decided to implement a solution from scratch, which can be found on [mcp_example](../src/mcp_example.py) and on its corresponding [`module`](../src/mcp_components/). Details about its architecture can be found on the [architecture document](./mcp-architecture.md).

Perhaps I got a little carried away and after implementing the STDIO transport, I thought it wouldn't be too hard implementing an HTTP transport later (which I ended up deciding fully delegate to Claude on [PR#7](https://github.com/lzfelix/building-with-claude/pull/7)).

Differently from the original course, and with insights from Claude, I used some tricks (that the course could have covered) to let the LLM auto-discovery available resources and tools. Also, I've implemented two MCP modules:

- The standard document server over stdio transport (very similar to the course. At time of writing, I realized I forgot to implement prompts, but still).
- A new calendar client that contains the same capabilities as seen in the [tools example](../src/tool_usage.py), but now over HTTP (something that wasn't covered by the course).


# Improvement steps

There are a few follow ups I'd like to implement in the future, such as integrating this example with a RAG application (to be developed) and propmt sampling (something I saw in the [MCP: Advanced Topics](https://anthropic.skilljar.com/model-context-protocol-advanced-topics)) course. I have an implementetion of this (developed as part of the course) sitting somewhere in my hard drive. It's just a matter of reserving some time to add this piece of code to the current code.