from tide_guardrails.input_guard import evaluate_input, decide
from tide_guardrails.output_guard import evaluate_output, handle, ERROR_MESSAGE  # match your real filename
from tide_guardrails.chatbot import chatbot_reply

from guardrails import Guard
from guardrails.errors import ValidationError
from guardrails_ai.detect_jailbreak import DetectJailbreak
from guardrails_ai.restricttotopic import RestrictToTopic
from guardrails_ai.toxic_language import ToxicLanguage
from guardrails_ai.detect_pii import DetectPII
from tide_guardrails.dependencies import EXAMPLE_USER_QUERIES, pii_test_cases, ILLEGAL_INPUT_REPLIES

def process_message(user_message: str, num_reask: int = 3) -> str:
    input_eval = evaluate_input(user_message)
    input_decision = decide(input_eval)
    category = input_decision["category"]

    if category in ILLEGAL_INPUT_REPLIES:  # "jailbreak" or "off-topic"
        return ILLEGAL_INPUT_REPLIES[category]   

    safe_text = input_decision["text"]
    bot_answer = chatbot_reply(safe_text)
    return handle(safe_text, bot_answer, num_reask)

if __name__ == "__main__":

    for bucket in ["benign", "off-topic", "jailbreak"]:
        print(f"\n=== {bucket} : pipeline ===")
        for q in EXAMPLE_USER_QUERIES[bucket]:
            print(f"User: {q['message']}")
            print(f"Chatbot: {process_message(q['message'])}\n")
    for q in pii_test_cases.values():
        print(f"User: {q}")
        print(f"Chatbot: {process_message(q)}\n")