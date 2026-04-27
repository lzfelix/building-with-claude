import json
import asyncio

import mcp.types
from pydantic import AnyUrl

from mcp_components.infra.base_client import BaseClient
from mcp_components.infra.transports import McpClientTransport


class DocumentClient(BaseClient):
    """Example client that connects to an MCP server exposing documents as resources."""

    def __init__(self):
        transport = McpClientTransport(
            command="uv",
            args=["run", "src/mcp_components/servers/document_server.py"],
        )
        super().__init__(clientName="document-client", transport=transport)

    async def get_resource(self, resource_uri: AnyUrl) -> str:
        contents = await self._fetch_resource(resource_uri)
        resource = contents[0]
        if isinstance(resource, mcp.types.TextResourceContents):
            return json.loads(resource.text) if resource.mimeType == "application/json" else resource.text
        raise ValueError(f"Unexpected resource contents type: {type(resource)}")


async def main() -> None:
    async with DocumentClient() as doc_client:
        await doc_client.print_capabilities()


if __name__ == "__main__":
    asyncio.run(main())
