import asyncio

from pydantic import AnyUrl

from mcp_components.infra.base_client import BaseClient
from mcp_components.infra.transports import HttpTransport


class ToolUsageClient(BaseClient):
    """MCP client connecting to the ToolUsageServer over StreamableHTTP.

    The server is spawned as a subprocess when connect() is called and
    terminated on cleanup, keeping the demo self-contained.
    """

    def __init__(self):
        transport = HttpTransport(
            url="http://localhost:8001/mcp",
            server_script="src/mcp_components/servers/tool_usage_server.py",
        )
        super().__init__(clientName="tool-usage-client", transport=transport)

    async def get_resource(self, resource_uri: AnyUrl) -> str:
        raise NotImplementedError("ToolUsageClient exposes no resources.")


async def main() -> None:
    async with ToolUsageClient() as client:
        await client.print_capabilities()


if __name__ == "__main__":
    asyncio.run(main())
