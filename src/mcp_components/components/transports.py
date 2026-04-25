from typing import Optional
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class McpClientTransport:
    """Base class for MCP clients that communicate over stdio transport.

    This class handles all the infrastructure for connecting to an MCP server
    over stdio, including spawning a child process running the MCP server and
    communicating with it via stdin/stdout using asyncio.
    
    It manages the connection lifecycle via an async context manager. Use
    'async with' to ensure the connection is properly cleaned up.
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
            stdio_client(server_params)
        )

        _stdio, _write = stdio_transport
        self._session = await self._exit_stack.enter_async_context(
            ClientSession(_stdio, _write)
        )
        await self.session.initialize()

class HttpClientTransport:
    """Placeholder for future HTTP transport implementation."""
    pass
