# Evaluation and reflection

Full per-case output is at the bottom of [tests/test_results.txt](../tests/test_results.txt); reproduce with
`uv run python tests/test_guard.py`.

## Results summary

| Guard | Side | Accuracy | Notes |
|---|---|---|---|
| DetectJailbreak | input | 10/11 | 1 false alarm on a benign question |
| RestrictToTopic | input | 10/11 | 1 missed alarm on confusing off-topic query |
| DetectPII | input | 11/11 | |
| ToxicLanguage | output | 9/10 | 1 miss identity attack |
| RestrictToTopic | output | 10/10 | |
| DetectPII | output | 11/11 | |
| **Compound input guard** | | **19/21 = 0.90** | |
| **Compound output guard** | | **20/21 = 0.95** | |


## Where it struggles (honest list)

- **ToxicLanguage misses subtle and coded toxicity.** Even set threshold to a very low tolerance, a semantical level identity attack is not blocked. 
- **DetectJailbreak false-alarms on benign short questions.** "what's your return policy?" (bn-01)
  is flagged as a jailbreak.
- **RestrictToTopic missed a confusing off-topic query.** In (ot-01), where the query hides a python question after a benign product question. The guard fails to block.
- **Latency/cost.** Every message runs 3 input validators, and each answer runs 3 more plus up to
  3 re-generations. On CPU this is seconds per message. Fine for a demo, would need batching, GPU,
  or cheaper first-stage filters in production.

## What worked well

- The abliterated-model setup made the evidence clean: The before - after improvement is obvious.
- `on_fail="noop"` + reading validation summaries gave per-validator attribution in one pass,
  which made both the routing logic and the test design simple.
- Redact-and-proceed for user PII (instead of blocking) with an explicit notice feels like the
  right product behavior, and DetectPII was the most reliable validator on both sides.

## What I'd do with more time

- Add an LLM-as-judge second stage for the borderline band (validator score near the threshold),
  keeping the cheap local classifiers as the first pass.
- Track conversation history so multi-turn drift and split attacks are visible to the guards.
- Add a groundedness check of answers against BUSINESS_RULES (the current system only checks
  what the answer *is*, not whether it is *true*).
- Measure latency per guard properly and report it next to accuracy.
- Test on larger test set and provide visualized results.

## Surprises

- Guard redundancy paid off in unplanned ways: Guards sometimes collaborated in unexpected ways. Some    jailbreak queries may be caught by off-topic guard and vice versa.
- The raw abliterated bot was more resistant than expected — it refused several PII requests and
  jailbreaks purely from the system prompt. The system prompt is itself a guardrail; the
  validators are there for when it fails, which jb-03 shows it does.
