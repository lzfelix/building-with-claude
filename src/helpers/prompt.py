from anthropic import Anthropic
from anthropic.types import Message, ToolParam


def run_prompt(
        client: Anthropic,
        prompt: str,
        model: str,
        stop_sequences: list[str] | None=None,
        assistant_prompt: str | None=None,
        max_tokens: int=10000,
        system_prompt: str | None=None) -> str:
    messages = [
        {"role": "user", "content": prompt}
    ]

    if assistant_prompt:
        messages.append({"role": "assistant", "content": assistant_prompt})

    response = multi_block_prompt(
        client,
        messages,
        model=model,
        stop_sequences=stop_sequences,
        max_tokens=max_tokens,
        system_prompt=system_prompt
    )
    return response.content[0].text

def multi_block_prompt(
        client: Anthropic,
        messages: list[dict],
        model: str,
        stop_sequences: list[str] | None=None,
        max_tokens: int=10000,
        system_prompt: str | None=None,
        tools: list[ToolParam] | None=None) -> Message:

    args = {
        "model": model,
        "max_tokens": max_tokens,
        "messages": messages
    }
    if system_prompt:
        args["system"] = system_prompt
    if stop_sequences:
        args["stop_sequences"] = stop_sequences
    if tools:
        args["tools"] = tools

    return client.messages.create(**args)
