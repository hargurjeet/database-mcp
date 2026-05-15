import os
import ollama
from dotenv import load_dotenv

load_dotenv()

OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")


def chat(messages: list[dict]) -> dict:
    return ollama.chat(model=OLLAMA_MODEL, messages=messages)
