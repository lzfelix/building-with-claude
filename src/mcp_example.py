import asyncio
from contextlib import AsyncExitStack

import anyio
import mcp.types
from pydantic import AnyUrl
from dotenv import load_dotenv
from anthropic import AsyncAnthropic

from mcp_components.components.base_client import BaseClient
from mcp_components.document_client import DocumentClient


MCP_TOOLS = [
    {
        "name": "read_resource",
        "description": "Fetch an MCP resource by URI",
        "input_schema": {
            "type": "object",
            "properties": {
                "client_name": {"type": "string"},
                "uri": {"type": "string"},
            },
            "required": ["client_name", "uri"],
        },
    },
    {
        "name": "call_tool",
        "description": "Call an MCP tool by name with arguments",
        "input_schema": {
            "type": "object",
            "properties": {
                "client_name": {"type": "string"},
                "tool_name": {"type": "string"},
                "arguments": {"type": "object"},
            },
            "required": ["client_name", "tool_name"],
        },
    },
]


class ChatLoop:
    def __init__(self, client: AsyncAnthropic, model_name: str, mcp_clients: list[BaseClient]) -> None:
        self._client = client
        self._model_name = model_name
        self._mcp_clients = mcp_clients

    async def _build_system_prompt(self) -> list:
        sections = []
        for client in self._mcp_clients:
            resources = await client.list_resources()
            templates = await client.list_resource_templates()
            tools = await client.list_tools()
            sections.append(
                f"Client: {client.clientName}\n"
                f"Resources: {', '.join(f'{r.uri}: {r.description}' for r in resources)}\n"
                f"Resource Templates: {', '.join(f'{rt.uriTemplate}: {rt.description}' for rt in templates)}\n"
                f"Tools: {', '.join(f'{t.name}: {t.description}' for t in tools)}"
            )
        return [{"type": "text", "text": "\n\n".join(sections), "cache_control": {"type": "ephemeral"}}]

    async def _dispatch_tool(self, block) -> str:
        client = next(c for c in self._mcp_clients if c.clientName == block.input["client_name"])
        if block.name == "read_resource":
            contents = await client._fetch_resource(AnyUrl(block.input["uri"]))
            resource = contents[0]
            return resource.text if isinstance(resource, mcp.types.TextResourceContents) else str(resource)
        if block.name == "call_tool":
            result = await client.session.call_tool(block.input["tool_name"], block.input.get("arguments", {}))
            return str(result)
        raise ValueError(f"Unknown tool: {block.name}")

    async def run_chat_loop(self) -> None:
        async with AsyncExitStack() as stack:
            for client in self._mcp_clients:
                await stack.enter_async_context(client)

            system = await self._build_system_prompt()

            messages = []
            while True:
                user_input = (await anyio.to_thread.run_sync(lambda: input("\nYou (or exit): "))).strip()
                if not user_input:
                    continue
                if user_input.lower() == "exit":
                    break

                messages.append({"role": "user", "content": user_input})
                response = await self._client.messages.create(
                    model=self._model_name,
                    max_tokens=1024,
                    system=system,
                    tools=MCP_TOOLS,
                    messages=messages,
                )

                while response.stop_reason == "tool_use":
                    tool_results = []
                    for block in response.content:
                        if block.type == "tool_use":
                            result = await self._dispatch_tool(block)
                            tool_results.append({"type": "tool_result", "tool_use_id": block.id, "content": result})
                    messages.append({"role": "assistant", "content": response.content})
                    messages.append({"role": "user", "content": tool_results})
                    response = await self._client.messages.create(
                        model=self._model_name,
                        max_tokens=1024,
                        system=system,
                        tools=MCP_TOOLS,
                        messages=messages,
                    )

                assistant_message = response.content[0].text
                messages.append({"role": "assistant", "content": assistant_message})
                print(f"\nAssistant: {assistant_message}")


if __name__ == "__main__":
    load_dotenv("config.env")
    model_name = "claude-haiku-4-5"
    client = AsyncAnthropic()

    print("""
    Suggestions of interesting prompts:
        - What are the depositions for today? (The LLM will auto-discover about the deposition file and return it)
        - How does the deposition relates to the technical report? (The LLM will read the deposition, read the technical report, and return a response relating the two)
    """)

    docs_client = DocumentClient()
    chat_loop = ChatLoop(client, model_name, mcp_clients=[docs_client])

    asyncio.run(chat_loop.run_chat_loop())
