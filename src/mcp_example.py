import dotenv
from anthropic import Anthropic
from helpers import prompt


if __name__ == "__main__":
    model = "claude-haiku-4-5"
    dotenv.load_dotenv()
    client = Anthropic()
