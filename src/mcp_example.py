import asyncio
import sys

import anyio
import dotenv
from anthropic import AsyncAnthropic
from mcp_components.document_client import DocumentClient


# async def discover_resources(client: DocumentClient) -> list[str]:
#     return await client.list_resources()



async def run_chat_loop(client: DocumentClient) -> None:
    dotenv.load_dotenv("config.env")
    anthropic = AsyncAnthropic()
    model = "claude-haiku-4-5"

    async with client:
        await client.print_capabilities()

        messages = []
        while True:
            user_input = (await anyio.to_thread.run_sync(lambda: input("\nYou: "))).strip()
            if not user_input:
                continue
            if user_input.lower() in ("exit", "quit"):
                break

            messages.append({"role": "user", "content": user_input})
            response = await anthropic.messages.create(
                model=model,
                max_tokens=1024,
                messages=messages,
            )
            assistant_message = response.content[0].text
            messages.append({"role": "assistant", "content": assistant_message})
            print(f"\nAssistant: {assistant_message}")


if __name__ == "__main__":
    docs_client = DocumentClient()
    asyncio.run(run_chat_loop(docs_client))
