import abc
import asyncio
from typing import Optional
from contextlib import AsyncExitStack

import httpx
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.streamable_http import streamablehttp_client


class ClientTransport(abc.ABC):
    """Abstract base for all MCP transport implementations.

    Provides the async context manager protocol once so subclasses don't repeat it.
    Subclasses must implement connect(), cleanup(), and the _session property.
    """

    async def __aenter__(self) -> "ClientTransport":
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.cleanup()

    @property
    @abc.abstractmethod
    def _session(self) -> ClientSession: ...

    @abc.abstractmethod
    async def connect(self) -> None: ...

    @abc.abstractmethod
    async def cleanup(self) -> None: ...


class StdioTransport(ClientTransport):
    """MCP client transport over stdio.

    Spawns the server as a child process and communicates via stdin/stdout.
    Manages the connection lifecycle via an async context manager — use
    'async with' to ensure the connection is properly cleaned up.
    """

    def __init__(self, command: str, args: list[str]):
        self._command = command
        self._args = args
        self._exit_stack = AsyncExitStack()
        self.__session: Optional[ClientSession] = None

    @property
    def _session(self) -> ClientSession:
        if self.__session is None:
            raise RuntimeError("Not connected. Use 'async with' or call connect() first.")
        return self.__session

    async def connect(self) -> None:
        server_params = StdioServerParameters(
            command=self._command,
            args=self._args
        )
        stdio_transport = await self._exit_stack.enter_async_context(
            stdio_client(server_params)
        )
        _stdio, _write = stdio_transport
        self.__session = await self._exit_stack.enter_async_context(
            ClientSession(_stdio, _write)
        )
        await self._session.initialize()

    async def cleanup(self) -> None:
        await self._exit_stack.aclose()
        self.__session = None


class HttpClientTransport(ClientTransport):
    """MCP client transport over StreamableHTTP.

    If server_script is provided, spawns the server as a subprocess (via
    'uv run <server_script>') and waits until the HTTP endpoint accepts
    connections before initialising the MCP session. The subprocess is
    terminated on cleanup.

    If server_script is None, the server is assumed to be already running at url.
    """

    def __init__(
        self,
        url: str,
        server_script: Optional[str] = None,
        retry_attempts: int = 10,
        retry_delay: float = 0.5,
    ):
        self._url = url
        self._server_script = server_script
        self._retry_attempts = retry_attempts
        self._retry_delay = retry_delay
        self._exit_stack = AsyncExitStack()
        self.__session: Optional[ClientSession] = None
        self._subprocess: Optional[asyncio.subprocess.Process] = None

    @property
    def _session(self) -> ClientSession:
        if self.__session is None:
            raise RuntimeError("Not connected. Use 'async with' or call connect() first.")
        return self.__session

    async def connect(self) -> None:
        if self._server_script is not None:
            self._subprocess = await asyncio.create_subprocess_exec(
                "uv", "run", self._server_script,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
            await self._wait_for_server()

        http_transport = await self._exit_stack.enter_async_context(
            streamablehttp_client(self._url)
        )
        _read, _write, _ = http_transport
        self.__session = await self._exit_stack.enter_async_context(
            ClientSession(_read, _write)
        )
        await self._session.initialize()

    async def cleanup(self) -> None:
        await self._exit_stack.aclose()
        self.__session = None
        if self._subprocess is not None:
            self._subprocess.terminate()
            await self._subprocess.wait()
            self._subprocess = None

    async def _wait_for_server(self) -> None:
        """Poll the server URL until it responds or the retry budget is exhausted."""
        async with httpx.AsyncClient() as client:
            for attempt in range(self._retry_attempts):
                try:
                    await client.get(self._url)
                    return
                except httpx.TransportError:
                    if attempt == self._retry_attempts - 1:
                        raise RuntimeError(
                            f"HTTP server at {self._url} did not become ready "
                            f"after {self._retry_attempts} attempts."
                        ) from None
                    await asyncio.sleep(self._retry_delay)
