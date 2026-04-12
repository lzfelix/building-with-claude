from anthropic import Anthropic


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

    args = {
        "model": model,
        "max_tokens": max_tokens,
        "messages": messages
    }
    if system_prompt:
        args["system"] = system_prompt
    if stop_sequences:
        args["stop_sequences"] = stop_sequences

    response = client.messages.create(**args)
    return response.content[0].text
