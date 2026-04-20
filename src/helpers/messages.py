from anthropic.types import Message


def add_message(role, messages, message):
    messages.append({
        "role": role,
        "content": message.content if isinstance(message, Message) else message
    })

def text_from_message(message):
    return "\n".join([b.text for b in message.content if b.type == "text"])
