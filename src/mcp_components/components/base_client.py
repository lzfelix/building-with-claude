
import abc

import mcp
from pydantic import AnyUrl

from mcp_components.components.transports import McpClientTransport


class BaseClient(McpClientTransport, abc.ABC):
    """MCP client that can list the capabilities exposed by the connected server.
    
    Ideally, this implementation could be extended to receive different underlying
    transport implementations (e.g. WebSocket, HTTP, etc.). For now, it just extends
    McpClientTransport for simplicity.

    If such an extension is implemented in the future, then the BaseClient can become
    the basis for any type of MCP client, delegating transport-specific details to the
    underlying transport classes, while still providing common functionality like
    listing capabilities.
    """

    def __init__(self, clientName: str, command: str, args: list[str]):
        super().__init__(command, args)
        self._clientName = clientName

    @property
    def clientName(self) -> str:
        return self._clientName

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

    async def _fetch_resource(self, uri: AnyUrl) -> list:
        response = await self.session.read_resource(uri)
        return response.contents

    @abc.abstractmethod
    async def get_resource(self, resource_name: str) -> str:
        ...
