from anthropic import Anthropic
from dotenv import load_dotenv


def add_user_message(messages, content):
    messages.append({
        "role": "user",
        "content": content
    })


def add_assistant_message(messages, content):
    messages.append({
        "role": "assistant",
        "content": content
    })


def chat(client: Anthropic, model: str, messages: list) -> str:
    system_prompt = "You talk like a university professor."

    message = client.messages.create(
        model=model,
        max_tokens=1000,
        messages=messages,
        system=system_prompt
    )
    return message.content[0].text


def stream_chat(client: Anthropic, model: str, messages: list):
    system_prompt = "You talk like a university professor."

    buffer = []
    with client.messages.stream(model=model, max_tokens=1000, messages=messages, system=system_prompt) as stream:
        for event in stream.text_stream:
            print(event, end="", flush=True)
            buffer.append(event)
    print()
    return stream.get_final_message()


if __name__ == "__main__":
    load_dotenv("config.env")

    client = Anthropic()
    model  = "claude-sonnet-4-0"
    messages = []

    add_user_message(messages, "Define quantum computing in one sentence.")
    answer = chat(client, model, messages)
    print(answer)

    add_assistant_message(messages, answer)
    add_user_message(messages, "Write another sentence")

    final_answer = chat(client, model, messages)
    print(final_answer)

    while True:
        new_input = input("Enter your message (or 'exit' to quit): ")
        if new_input.lower() == 'exit':
            break
        add_user_message(messages, new_input)
        response = stream_chat(client, model, messages)
        add_assistant_message(messages, response)
