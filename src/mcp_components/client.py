import asyncio
from typing import Optional
from contextlib import AsyncExitStack

import mcp
from mcp import ClientSession, StdioServerParameters


class BaseMCPClient:
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
        await self._session.initialize()


async def main() -> None:
    async with BaseMCPClient(
        command="uv",
        args=["run", "src/mcp_components/server.py"],
    ) as _client:
        pass


if __name__ == "__main__":
    asyncio.run(main())
