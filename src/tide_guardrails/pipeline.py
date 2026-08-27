from tide_guardrails.input_guard import evaluate_input, decide, PII_NOTICE
from tide_guardrails.output_guard import handle
from tide_guardrails.chatbot import chatbot_reply
from tide_guardrails.dependencies import EXAMPLE_USER_QUERIES, pii_test_cases, ILLEGAL_INPUT_REPLIES


def process_message(user_message: str, num_reask: int = 3) -> str:
    input_decision = decide(evaluate_input(user_message))
    category = input_decision["category"]
    prefix = PII_NOTICE if input_decision["pii_redacted"] else ""

    if category in ILLEGAL_INPUT_REPLIES:  # "jailbreak" or "off-topic"
        return prefix + ILLEGAL_INPUT_REPLIES[category]

    safe_text = input_decision["text"]
    bot_answer = chatbot_reply(safe_text)
    return prefix + handle(safe_text, bot_answer, num_reask)


if __name__ == "__main__":
    for bucket in ["benign", "off-topic", "jailbreak"]:
        print(f"\n=== {bucket} : pipeline ===")
        for q in EXAMPLE_USER_QUERIES[bucket]:
            print(f"User: {q['message']}")
            print(f"Chatbot: {process_message(q['message'])}\n")
    for q in pii_test_cases.values():
        print(f"User: {q}")
        print(f"Chatbot: {process_message(q)}\n")
