from guardrails import Guard
from guardrails.errors import ValidationError
from guardrails_ai.toxic_language import ToxicLanguage
from guardrails_ai.restricttotopic import RestrictToTopic
from guardrails_ai.detect_pii import DetectPII
from tide_guardrails.dependencies import EXAMPLE_USER_QUERIES, pii_test_cases
from tide_guardrails.chatbot import chatbot_reply

ERROR_MESSAGE = "Sorry, there was an error processing your request. Please try again later or contact a human support."

output_guard = Guard().use(ToxicLanguage(threshold=0.75, device="cpu", use_local=True, on_fail="noop"),
                           RestrictToTopic(valid_topics=["customer service"], disable_llm=True,
                                             disable_classifier=False, use_local=True, on_fail="noop",),
                            DetectPII(pii_entities=["EMAIL_ADDRESS", "PHONE_NUMBER",
                                                    "US_BANK_NUMBER", "US_SSN", "US_PASSPORT", "US_DRIVER_LICENSE"], on_fail="noop", use_local=True))


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
    if not isinstance(num_reask, int) or num_reask < 1:
        raise ValueError(f"num_reask must be a positive integer, got {num_reask!r}")
    eval_result = evaluate_output(bot_answer)
    if not eval_result["triggered"]:
        return bot_answer
    else:
        num_reasked = 0
        for i in range(num_reask):
            new_prompt = ""
            if "ToxicLanguage" in eval_result["triggered"]:
                new_prompt = new_prompt + "The previous response was flagged as containing toxic language. Please provide a new response that is safe and appropriate for customer service."
            if "RestrictToTopic" in eval_result["triggered"]:
                new_prompt = new_prompt + "The previous response was flagged as off-topic. Please provide a new response that is relevant to customer service."
            if "DetectPII" in eval_result["triggered"]:
                new_prompt = new_prompt + "The previous response was flagged as containing sensitive information. Please provide a new response that does not contain any personal data."
            new_prompt = f"For the user message: '{user_message}', you provided the following response: '{bot_answer}'. {new_prompt}"    
            new_answer = chatbot_reply(new_prompt)
            num_reasked += 1
            new_eval_result = evaluate_output(new_answer)
            if not new_eval_result["triggered"]:
                return new_answer
            else:
                if num_reasked >= num_reask:
                    return ERROR_MESSAGE
                else:
                    eval_result = new_eval_result
                    bot_answer = new_answer