import os
from tool_usage import tools
from dotenv import load_dotenv
from anthropic import Anthropic
from anthropic.types import Message


_all_tools = [
    tools.get_current_datetime_schema,
    tools.add_duration_to_datetime_schema,
    tools.set_reminder_schema,
    tools.get_reminders_schema
]


def chat(client: Anthropic, model: str, messages: list, tools: list):
    system_prompt = "You are a helpful assistant that provides the current date and time when asked."

    result = client.messages.create(
        model=model,
        max_tokens=1000,
        messages=messages,
        system=system_prompt,
        tools=tools
    )
    return result


def add_message(role, messages, message):
    messages.append({
        "role": role,
        "content": message.content if isinstance(message, Message) else message
    })


def text_from_message(message):
    return "\n".join([b.text for b in message.content if b.type == "text"])


def run_tool(tool_name, tool_input):
    if tool_name == "get_current_datetime":
        return tools.get_current_datetime(**tool_input)
    elif tool_name == "add_duration_to_datetime":
        return tools.add_duration_to_datetime(**tool_input)
    elif tool_name == "set_reminder":
        return tools.set_reminder(**tool_input)
    elif tool_name == "get_reminders":
        return tools.get_reminders()
    else:
        raise ValueError(f"Unknown tool: {tool_name}")


def run_tools(message):
    tool_requests = [
        block for block in message.content if block.type == "tool_use"
    ]
    tool_result_blocks = []

    for tool_request in tool_requests:
        try:
            result = run_tool(tool_request.name, tool_request.input)
            tool_result_blocks.append({
                "type": "tool_result",
                "tool_use_id": tool_request.id,
                "content": result,
                "is_error": False
            })
        except Exception as e:
            tool_result_blocks.append({
                "type": "tool_result",
                "tool_use_id": tool_request.id,
                "content": str(e),
                "is_error": True
            })
    return tool_result_blocks


def run_conversation(client, model, messages):
    while True:
        response = chat(client, model, messages, tools=_all_tools)
        add_message("assistant", messages, response)
        
        text_response = text_from_message(response)

        if response.stop_reason != "tool_use":
            print(f"\tFinished intermediate steps.")
            print(f"Agent: {text_response}")
            break
        else:
            print(f"\tIntermediate response: {text_response if text_response else '[No text response]'}")

        tool_result_blocks = run_tools(response)
        add_message("user", messages, tool_result_blocks)
    return messages


if __name__ == "__main__":
    model = "claude-haiku-4-5"
    load_dotenv(os.path.join(os.path.dirname(__file__), "..", "config.env"))
    client = Anthropic()

    print("""
        I'm an appointment scheduler assistant. I can figure what date is today, do basic date arithmetic,
          and set reminders for you. Try asking me to set a reminder for something in the future!

        I'll start by setting a simple reminder for you, and then you can try with your own requests.
          Just type 'exit' to quit.
    """)
    conversation_history = []
    user_prompt = "Set me a reminder 3 days from now to do groceries."

    while user_prompt != "exit":
        if user_prompt:
            print(f"User: {user_prompt}")
        else:
            user_prompt = input("User (or 'exit'): ")

        if user_prompt == "exit":
            break

        conversation_history.append({"role": "user", "content": user_prompt})
        run_conversation(client, model, conversation_history)
        user_prompt = None
    print("Bye.")
