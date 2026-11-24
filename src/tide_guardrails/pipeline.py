from tide_guardrails.input_guard import evaluate_input, decide, PII_NOTICE
from tide_guardrails.output_guard import handle
from tide_guardrails.chatbot import chatbot_reply, format_context
from tide_guardrails.dependencies import EXAMPLE_USER_QUERIES, ILLEGAL_INPUT_REPLIES
from tide_guardrails.rag.retrieval import retrieve, DEFAULT_K, MIN_SCORE


def retrieve_context(message: str, debug: bool = False) -> str:
    """Retrieve the top chunks for a message and format them for the prompt.
    Chunks scoring below MIN_SCORE are dropped, so a message the knowledge base
    can't answer gets an explicit "nothing found" context instead of loosely
    related chunks."""
    results = retrieve(message, k=DEFAULT_K, min_score=MIN_SCORE)
    if debug:
        print("  [retrieved] " + (", ".join(f"{c.chunk_id} {s:.2f}" for c, s in results) or "nothing"))
    return format_context(results)


def process_message(user_message: str, num_reask: int = 3, debug: bool = False) -> str:
    input_decision = decide(evaluate_input(user_message))
    category = input_decision["category"]
    prefix = PII_NOTICE if input_decision["pii_redacted"] else ""

    if category in ILLEGAL_INPUT_REPLIES:  # "jailbreak" or "off-topic"
        return prefix + ILLEGAL_INPUT_REPLIES[category]

    safe_text = input_decision["text"]
    context = retrieve_context(safe_text, debug)   # once per user message, on the redacted text
    bot_answer = chatbot_reply(safe_text, context)
    return prefix + handle(safe_text, bot_answer, num_reask, context)


if __name__ == "__main__":
    for bucket in ["benign", "off-topic", "jailbreak", "PII-exposure"]:
        print(f"\n=== {bucket} : pipeline ===")
        for q in EXAMPLE_USER_QUERIES[bucket]:
            print(f"User: {q['message']}")
            print(f"Chatbot: {process_message(q['message'], debug=True)}\n")
