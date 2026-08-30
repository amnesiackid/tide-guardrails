from guardrails import Guard
from guardrails_ai.toxic_language import ToxicLanguage
from guardrails_ai.restricttotopic import RestrictToTopic
from guardrails_ai.detect_pii import DetectPII
from tide_guardrails.input_guard import PII_ENTITIES
from tide_guardrails.chatbot import chatbot_reply

ERROR_MESSAGE = "Sorry, there was an error processing your request. Please try again later or contact a human support."

REASK_INSTRUCTIONS = {
    "ToxicLanguage": "The previous response was flagged as containing toxic language. Please provide a new response that is safe and appropriate for customer service.",
    "RestrictToTopic": "The previous response was flagged as off-topic. Please provide a new response that is relevant to customer service.",
    "DetectPII": "The previous response was flagged as containing sensitive information. Please provide a new response that does not contain any personal data.",
}

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


def handle(user_message: str, bot_answer: str, num_reask: int) -> str:
    """Return bot_answer if it passes the output guard; otherwise re-ask the
    model up to num_reask times with the failure reasons, then give up."""
    if not isinstance(num_reask, int) or num_reask < 1:
        raise ValueError(f"num_reask must be a positive integer, got {num_reask!r}")
    eval_result = evaluate_output(bot_answer)
    if not eval_result["triggered"]:
        return bot_answer
    for _ in range(num_reask):
        feedback = " ".join(REASK_INSTRUCTIONS[name]
                            for name in REASK_INSTRUCTIONS
                            if name in eval_result["triggered"])
        new_prompt = (f"For the user message: '{user_message}', you provided the "
                      f"following response: '{bot_answer}'. {feedback}")
        bot_answer = chatbot_reply(new_prompt)
        eval_result = evaluate_output(bot_answer)
        if not eval_result["triggered"]:
            return bot_answer
    return ERROR_MESSAGE
