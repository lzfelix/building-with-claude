import abc

import mcp
from pydantic import AnyUrl

from mcp_components.infra.transports import ClientTransport


class BaseClient(abc.ABC):
    """Generic MCP client adapter.

    Accepts any ClientTransport implementation so the same BaseClient subclass
    hierarchy works over stdio and HTTP without changes to domain subclasses.

    BaseClient accesses self._transport._session directly — this is intentional.
    BaseClient lives in the same infra/ package and is the only non-transport
    code that needs the raw session.
    """

    def __init__(self, clientName: str, transport: ClientTransport):
        self._clientName = clientName
        self._transport = transport

    async def __aenter__(self) -> "BaseClient":
        await self._transport.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self._transport.cleanup()

    @property
    def clientName(self) -> str:
        return self._clientName

    async def list_tools(self) -> list[mcp.types.Tool]:
        result = await self._transport._session.list_tools()
        return result.tools

    async def list_resources(self) -> list[mcp.types.Resource]:
        result = await self._transport._session.list_resources()
        return result.resources

    async def list_prompts(self) -> list[mcp.types.Prompt]:
        result = await self._transport._session.list_prompts()
        return result.prompts

    async def list_resource_templates(self) -> list[mcp.types.ResourceTemplate]:
        result = await self._transport._session.list_resource_templates()
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
        response = await self._transport._session.read_resource(uri)
        return response.contents

    async def call_tool(self, tool_name: str, arguments: dict) -> mcp.types.CallToolResult:
        return await self._transport._session.call_tool(tool_name, arguments)

    @abc.abstractmethod
    async def get_resource(self, resource_uri: AnyUrl) -> str:
        ...
