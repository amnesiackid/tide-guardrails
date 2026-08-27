"""
Guard tests: each validator alone, then the compound guards.
Every case expects either "the responsible validator fires" or, for benign, "nothing fires".
Accuracy = how often that expectation held.

    uv run python tests/test_guard.py
"""

import os, logging, warnings

# must be set before guardrails imports, or they have no effect
os.environ["OTEL_SDK_DISABLED"] = "true"
logging.getLogger("presidio-analyzer").setLevel(logging.ERROR)
warnings.filterwarnings("ignore")

from guardrails import Guard
from guardrails_ai.detect_jailbreak import DetectJailbreak
from guardrails_ai.restricttotopic import RestrictToTopic
from guardrails_ai.detect_pii import DetectPII
from guardrails_ai.toxic_language import ToxicLanguage

from test_cases import EXAMPLE_USER_QUERIES, BOT_RESPONSES, pii_test_cases
from tide_guardrails.input_guard import evaluate_input, PII_ENTITIES
from tide_guardrails.output_guard import evaluate_output


# Same config as production, except on_fail="noop" so nothing raises.
SINGLE = {
    "DetectJailbreak": Guard().use(
        DetectJailbreak(threshold=0.75, device="cpu", use_local=True, on_fail="noop")),
    "RestrictToTopic": Guard().use(
        RestrictToTopic(valid_topics=["customer service"], disable_llm=True,
                        use_local=True, disable_classifier=False, on_fail="noop")),
    "DetectPII": Guard().use(
        DetectPII(pii_entities=PII_ENTITIES, use_local=True, on_fail="noop")),
    "ToxicLanguage": Guard().use(
        ToxicLanguage(threshold=0.75, device="cpu", use_local=True, on_fail="noop")),
}

# Input-side PII-exposure is left out: those messages ask for PII, they contain none,
# so no input validator can catch them. LOCATION is left out for the same reason —
# it isn't in PII_ENTITIES.
INPUT_CASES = {
    "benign":    EXAMPLE_USER_QUERIES["benign"],
    "jailbreak": EXAMPLE_USER_QUERIES["jailbreak"],
    "off-topic": EXAMPLE_USER_QUERIES["off-topic"],
    "PII":       EXAMPLE_USER_QUERIES["PII-exposure"],
}

INPUT_GUARD_FOR = {"benign": None, "jailbreak": "DetectJailbreak",
                   "off-topic": "RestrictToTopic", "PII": "DetectPII"}

OUTPUT_GUARD_FOR = {"benign": None, "off-topic": "RestrictToTopic",
                    "PII-exposure": "DetectPII", "toxicity": "ToxicLanguage"}


def fired(guard, text):
    out = guard.validate(text)
    return any(s.validator_status == "fail" for s in out.validation_summaries)


def test_single(side, cases, validators, guard_for):
    print(f"\n=== {side}: each validator alone ===")
    for name in validators:
        ok = total = 0
        for bucket, items in cases.items():
            owner = guard_for[bucket]
            if owner is not None and owner != name:
                continue                      # not this validator's bucket
            should_fire = owner == name       # False for benign
            for c in items:
                did = fired(SINGLE[name], c["message"])
                total += 1
                if did == should_fire:
                    ok += 1
                else:
                    what = "missed" if should_fire else "false alarm"
                    print(f"  {name} {what}: [{c['id']}] {c['message'][:45]}")
        print(f"  {name}: {ok}/{total} = {ok / total:.2f}")


def test_compound(side, cases, evaluate, guard_for):
    print(f"\n=== {side}: compound guard ===")
    ok = total = 0
    for bucket, items in cases.items():
        print(f"-- {bucket} --")
        for c in items:
            triggered = evaluate(c["message"])["triggered"]
            owner = guard_for[bucket]
            correct = (not triggered) if owner is None else (owner in triggered)
            total += 1
            ok += correct
            print(f"  {'ok   ' if correct else 'WRONG'} [{c['id']}] "
                  f"({','.join(triggered) or '-'}) {c['message'][:40]}")
    print(f"  {side}: {ok}/{total} = {ok / total:.2f}")


if __name__ == "__main__":
    test_single("INPUT", INPUT_CASES, ["DetectJailbreak", "RestrictToTopic", "DetectPII"],
                INPUT_GUARD_FOR)
    test_single("OUTPUT", BOT_RESPONSES, ["ToxicLanguage", "RestrictToTopic", "DetectPII"],
                OUTPUT_GUARD_FOR)

    test_compound("INPUT", INPUT_CASES, evaluate_input, INPUT_GUARD_FOR)
    test_compound("OUTPUT", BOT_RESPONSES, evaluate_output, OUTPUT_GUARD_FOR)