import asyncio
from typing import Optional
from contextlib import AsyncExitStack

import mcp
import mcp.types
from mcp import ClientSession, StdioServerParameters


class BaseStdioMcpClient:
    """Base class for MCP clients that communicate over stdio transport.

    Spawns a child process running the MCP server and communicates with it via
    stdin/stdout using asyncio. Manages the connection lifecycle via an async
    context manager. Use 'async with' to ensure the connection is properly
    cleaned up.
    """
    def __init__(
        self,
        command: str,
        args: list[str]
    ):
        self._command = command
        self._args = args

        self._exit_stack = AsyncExitStack()
        self._session: Optional[ClientSession] = None

    async def cleanup(self):
        await self._exit_stack.aclose()
        self._session = None

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.cleanup()
    
    @property
    def session(self) -> ClientSession:
        if self._session is None:
            raise RuntimeError("Not connected. Use 'async with' or call connect() first.")
        return self._session

    async def connect(self):
        server_params = StdioServerParameters(
            command=self._command,
            args=self._args
        )

        stdio_transport = await self._exit_stack.enter_async_context(
            mcp.client.stdio.stdio_client(server_params)
        )

        _stdio, _write = stdio_transport
        self._session = await self._exit_stack.enter_async_context(
            ClientSession(_stdio, _write)
        )
        await self.session.initialize()


class TrivialClient(BaseStdioMcpClient):
    """MCP client that can list the capabilities exposed by the connected server."""
    
    async def list_tools(self) -> list[mcp.types.Tool]:
        result = await self.session.list_tools()
        return result.tools
    
    async def list_resources(self) -> list[mcp.types.Resource]:
        result = await self.session.list_resources()
        return result.resources
    
    async def list_prompts(self) -> list[mcp.types.Prompt]:
        result = await self.session.list_prompts()
        return result.prompts

    async def list_resource_templates(self) -> list[mcp.types.ResourceTemplate]:
        result = await self.session.list_resource_templates()
        return result.resourceTemplates

    async def print_capabilities(self) -> None:
        tools = await self.list_tools()
        resources = await self.list_resources()
        resource_templates = await self.list_resource_templates()
        prompts = await self.list_prompts()

        print(f"Tools ({len(tools)}):", *[f"  - {t.name}" for t in tools], sep="\n")
        print(f"Resources ({len(resources)}):", *[f"  - {r.uri}" for r in resources], sep="\n")
        print(f"Resource Templates ({len(resource_templates)}):", *[f"  - {rt.uriTemplate}" for rt in resource_templates], sep="\n")
        print(f"Prompts ({len(prompts)}):", *[f"  - {p.name}" for p in prompts], sep="\n")


async def main() -> None:
    async with TrivialClient(
        command="uv",
        args=["run", "src/mcp_components/server.py"],
    ) as _client:
        await _client.print_capabilities()


if __name__ == "__main__":
    asyncio.run(main())
