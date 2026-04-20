import os
from tool_usage import tools
from dotenv import load_dotenv
from anthropic import Anthropic
from helpers import messages
from helpers.prompt import multi_block_prompt


def chat(client: Anthropic, model: str, conversation: list, tools: list):
    system_prompt = "You are a helpful assistant that provides the current date and time when asked."
    return multi_block_prompt(
        client,
        conversation,
        model=model,
        system_prompt=system_prompt,
        tools=tools
    )


def run_conversation(client, model, conversation):
    while True:
        response = chat(client, model, conversation, tools=tools.registry.schemas)
        messages.add_message("assistant", conversation, response)

        text_response = messages.text_from_message(response)

        if response.stop_reason != "tool_use":
            print(f"\tFinished intermediate steps.")
            print(f"Agent: {text_response}")
            break
        else:
            print(f"\tIntermediate response: {text_response if text_response else '[No text response]'}")

        tool_result_blocks = tools.registry.run_tools(response)
        messages.add_message("user", conversation, tool_result_blocks)
    return conversation


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

        messages.add_message("user", conversation_history, user_prompt)
        run_conversation(client, model, conversation_history)
        user_prompt = None
    print("Bye.")
