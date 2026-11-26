from guardrails import Guard
from guardrails_ai.toxic_language import ToxicLanguage
from guardrails_ai.restricttotopic import RestrictToTopic
from guardrails_ai.detect_pii import DetectPII
from tide_guardrails.input_guard import PII_ENTITIES
from tide_guardrails.chatbot import chatbot_reply, NO_CONTEXT
from tide_guardrails.rag.chunking import Chunk
from tide_guardrails.rag_guard import check_grounded

ERROR_MESSAGE = "Sorry, there was an error processing your request. Please try again later or contact a human support."

REASK_INSTRUCTIONS = {
    "ToxicLanguage": "The previous response was flagged as containing toxic language. Please provide a new response that is safe and appropriate for customer service.",
    "RestrictToTopic": "The previous response was flagged as off-topic. Please provide a new response that is relevant to customer service.",
    "DetectPII": "The previous response was flagged as containing sensitive information. Please provide a new response that does not contain any personal data.",
    # Worded without "CONTEXT": with it, the model started writing "The CONTEXT only
    # mentions ...", which is never entailed, and looped into the error message.
    "Groundedness": "The previous response stated numbers or facts that the store information does not support. Please answer again stating only facts from the store information, plainly, without hedging and without referring to the information itself.",
}

GROUNDING_FALLBACK = ("I'm a chatbot and may make mistakes, so here is the relevant part of our "
                      "store information as written:\n\n{title} > {heading}\n{text}")
NO_INFO_REPLY = "I'm a chatbot, and I don't have that information. Please contact human support."

output_guard = Guard().use(
    ToxicLanguage(threshold=0.1, device="cpu", use_local=True, on_fail="noop",),
    RestrictToTopic(valid_topics=["customer service", "product information"], disable_llm=True,
                    disable_classifier=False, use_local=True, on_fail="noop",),
    DetectPII(pii_entities=PII_ENTITIES, on_fail="noop", use_local=True),
)


def evaluate_output(text: str) -> dict:
    out = output_guard.validate(text)
    triggered = {
        s.validator_name: s.failure_reason
        for s in out.validation_summaries
        if s.validator_status == "fail"
    }
    return {
        "triggered": triggered,
    }


def check_answer(answer: str, chunks: list[Chunk] | None = None) -> dict:
    """Output guard validators, plus the groundedness check when `chunks` is given."""
    triggered = dict(evaluate_output(answer)["triggered"])
    best_chunk = None
    if chunks is not None:
        grounding = check_grounded(answer, chunks)
        if not grounding["grounded"]:
            triggered["Groundedness"] = f"unsupported: {grounding['unsupported']}"
            best_chunk = grounding["best_chunk"]
    return {"triggered": triggered, "best_chunk": best_chunk}


def handle(user_message: str, bot_answer: str, num_reask: int, context: str = NO_CONTEXT,
           chunks: list[Chunk] | None = None) -> str:
    """Return bot_answer if it passes the output guard; otherwise re-ask the
    model up to num_reask times with the failure reasons, then give up.

    Every re-ask reuses the context retrieved for the original user message.
    Retrieving again on the re-ask prompt would search with the bad answer and
    the feedback text, and return the wrong chunks. `chunks` (the retrieved
    chunks behind `context`) turns on the groundedness check.

    Groundedness gets one re-ask, not num_reask: when a re-asked answer still
    fails ONLY groundedness, we return the top retrieved chunk verbatim, which is
    grounded by construction, instead of looping into the error message."""
    if not isinstance(num_reask, int) or num_reask < 1:
        raise ValueError(f"num_reask must be a positive integer, got {num_reask!r}")
    eval_result = check_answer(bot_answer, chunks)
    if not eval_result["triggered"]:
        return bot_answer
    for attempt in range(num_reask):
        if attempt >= 1 and set(eval_result["triggered"]) == {"Groundedness"}:
            best = eval_result["best_chunk"]
            if best is None:
                return NO_INFO_REPLY
            return GROUNDING_FALLBACK.format(title=best.title, heading=best.heading, text=best.text)
        feedback = " ".join(REASK_INSTRUCTIONS[name]
                            for name in REASK_INSTRUCTIONS
                            if name in eval_result["triggered"])
        # The re-ask prompt is English; without the last sentence a Chinese
        # question flagged once got its final answer in English.
        new_prompt = (f"For the user message: '{user_message}', you provided the "
                      f"following response: '{bot_answer}'. {feedback} "
                      f"Reply in the same language as the user message.")
        bot_answer = chatbot_reply(new_prompt, context)
        eval_result = check_answer(bot_answer, chunks)
        if not eval_result["triggered"]:
            return bot_answer
    return ERROR_MESSAGE
