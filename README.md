# Building with Claude

Just me following Skilljar's Claude [Building with Claude](https://anthropic.skilljar.com/claude-with-the-anthropic-api) while I add a bit of experimentation and personal touch along the way.

# How to use

1. Create a `config.env` file with your `ANTHROPIC_API_KEY`. Use the `config.env.example` as a guide.
2. Install dependencies with `uv sync`.
3. Now you can run the examples as detailed in the next section.

## Available examples

Detailed write-ups for each example can be found in the [`docs/`](docs/) directory.
In order to run the examples, from the prpoject root folder, issue `uv run src/<script>.py`.

| Example | Concept | Description | Source | Report |
|---|---|---|---|---|
| LeetCode Evaluator | prompt engineering | Evaluates an LLM-generated Python solver across LeetCode-style problems using a multi-stage grading pipeline. | [src](src/leetcode_evaluator.py) | [report](docs/leetcode-evaluator.md) |
| SQL Review | prompt engineering | Evaluates an LLM-generated PostgreSQL query solver across tasks from simple SELECT to window functions. | [src](src/sql_review.py) | [report](docs/sql-review.md) |
| Reminder Assistant | multi turn chat + tool call | A multi-turn chatbot that uses tools to get the current datetime, do date arithmetic, and manage in-memory reminders. | [src](src/tool_usage.py) | [report](docs/tool_usage.md) |
| Fire Risk Assessment | image processing | Evaluates wildfire risk from property images using Claude's vision capabilities, assigning a 1–4 risk rating across six inspection criteria. | [src](src/fire_risk_assessment.py) | [report](docs/fire-risk-assessment.md) |
| Reminder Assistant with Caching | prompt caching | Extends the Reminder Assistant with prompt caching, printing cache creation and read tokens on each turn to demonstrate how a stable system prompt and tool list are served from cache across a conversation. | [src](src/tool_usage_with_cache.py) | [report](docs/tool_usage_with_cache.md) |
| MCP Document Assistant | MCP client/server + FastMCP | A multi-turn chatbot backed by a FastMCP document server, where the LLM autonomously discovers and retrieves available resources by treating MCP capabilities as tool calls rather than hardcoded fetch logic.<br><br>This demo extends considerably what's presented in the course module by implementing auto-resource discovery, HTTP/Stdio transports, and a chat loop that can interact with multiple clients at once. | [src](src/mcp_example.py) | <br><br>[report](docs/mcp-module-comments.md)<br><br>[LLM-driven discovery in MCP](docs/mcp-llm-driven-discovery.md)<br><br>[architecture](docs/mcp-architecture.md) |
| Teaching Assistant | prompt caching + multi-turn chat + message streaming + workflows | An interactive quiz session driven by your own study notes. The notes are loaded as a cached system prompt; the LLM identifies the main topics, lets you pick which ones to cover, then asks adaptive questions: harder when you're doing well, easier when you're struggling. Also, it shows a section report after each topic. | [src](src/teaching_assistant.py) | — |
