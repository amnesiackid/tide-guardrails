import threading
threading.stack_size(16 * 1024 * 1024)

import os, logging, warnings


os.environ["OTEL_SDK_DISABLED"] = "true"
logging.getLogger("presidio-analyzer").setLevel(logging.ERROR)
warnings.filterwarnings("ignore")

from tide_guardrails.pipeline import process_message
from tide_guardrails.chatbot import chatbot_reply

def main(message: str, use_guards=True, num_reask=3):
    if use_guards is True:
        response = process_message(message, num_reask=num_reask)
    else:
        response = chatbot_reply(message)
    return response

def choose_mode() -> bool:
    """Ask once which mode to run in. Returns True for guarded pipeline, False for raw."""
    while True:
        choice = input("Use the guarded pipeline or the raw abliterate bot? [pipeline/raw]: ").strip().lower()
        if choice in ("pipeline", "p"):
            return True
        if choice in ("raw", "r"):
            return False
        print("Please type 'pipeline' or 'raw'.")

def run():
    print("=== Chatbot ===")
    use_guards = choose_mode()
    label = "guarded pipeline" if use_guards else "raw abliterate bot (no guards)"
    print(f"Mode: {label}. Type 'quit' to exit.\n")

    while True:
        message = input("You: ").strip()
        if message.lower() in ("quit", "exit"):
            break
        if not message:
            continue
        response = main(message, use_guards=use_guards)
        print(f"Bot: {response}\n")

if __name__ == "__main__":
    run()