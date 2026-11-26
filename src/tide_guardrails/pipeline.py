from tide_guardrails.input_guard import evaluate_input, decide, PII_NOTICE
from tide_guardrails.output_guard import handle
from tide_guardrails.chatbot import chatbot_reply, format_context
from tide_guardrails.dependencies import EXAMPLE_USER_QUERIES, ILLEGAL_INPUT_REPLIES
from tide_guardrails.rag.retrieval import retrieve, DEFAULT_K, MIN_SCORE
from tide_guardrails.rag_guard import screen_chunks

# RAG-specific defenses (Phase 5). PHASE4 = none, for before/after comparisons.
#   chunk_guard     drop retrieved chunks that give orders to the assistant
#   topic_override  let a message the topic classifier flagged through if the KB answers it
#   grounding       re-ask when the answer states numbers the retrieved chunks don't support
PHASE4 = frozenset()
PHASE5 = frozenset({"chunk_guard", "topic_override", "grounding"})
DEFAULT_DEFENSES = PHASE5

# A message RestrictToTopic flagged as off-topic proceeds if its top-1 retrieval
# score reaches this. Measured: true off-topic messages top out at 0.465, the 22
# answerable questions the classifier wrongly flagged start at 0.550 (see the
# Phase 5 results in docs/rag-learning-plan.md). Never applied to jailbreaks:
# real jailbreaks score 0.51-0.59 because they mention returns and products.
ON_TOPIC_SCORE = 0.52


def retrieve_chunks(message: str, defenses=DEFAULT_DEFENSES, debug: bool = False):
    """Top chunks for a message, above MIN_SCORE, screened for injections if enabled."""
    results = retrieve(message, k=DEFAULT_K, min_score=MIN_SCORE)
    if "chunk_guard" in defenses:
        results, dropped = screen_chunks(results)
        if debug and dropped:
            print("  [chunk guard dropped] " + ", ".join(c.chunk_id for c, _ in dropped))
    if debug:
        print("  [retrieved] " + (", ".join(f"{c.chunk_id} {s:.2f}" for c, s in results) or "nothing"))
    return results


def retrieve_context(message: str, debug: bool = False, defenses=DEFAULT_DEFENSES) -> str:
    """Retrieve and format the context for a message. Below MIN_SCORE the context
    says explicitly that nothing was found, instead of loosely related chunks."""
    return format_context(retrieve_chunks(message, defenses, debug))


def process_message(user_message: str, num_reask: int = 3, debug: bool = False,
                    defenses=DEFAULT_DEFENSES) -> str:
    input_decision = decide(evaluate_input(user_message))
    category = input_decision["category"]
    prefix = PII_NOTICE if input_decision["pii_redacted"] else ""
    safe_text = input_decision["text"]

    results = None
    if category == "off-topic" and "topic_override" in defenses:
        # Retrieval runs on the redacted text either way, once per message.
        results = retrieve_chunks(safe_text, defenses, debug)
        if results and results[0][1] >= ON_TOPIC_SCORE:
            if debug:
                print(f"  [topic override] top-1 {results[0][1]:.2f} >= {ON_TOPIC_SCORE}")
            category = "safe"

    if category in ILLEGAL_INPUT_REPLIES:  # "jailbreak" (never overridden) or "off-topic"
        return prefix + ILLEGAL_INPUT_REPLIES[category]

    if results is None:
        results = retrieve_chunks(safe_text, defenses, debug)
    context = format_context(results)
    chunks = [c for c, _ in results] if "grounding" in defenses else None
    bot_answer = chatbot_reply(safe_text, context)
    return prefix + handle(safe_text, bot_answer, num_reask, context, chunks)


if __name__ == "__main__":
    for bucket in ["benign", "off-topic", "jailbreak", "PII-exposure"]:
        print(f"\n=== {bucket} : pipeline ===")
        for q in EXAMPLE_USER_QUERIES[bucket]:
            print(f"User: {q['message']}")
            print(f"Chatbot: {process_message(q['message'], debug=True)}\n")
