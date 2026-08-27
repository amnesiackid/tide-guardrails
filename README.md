# tide-guardrails

Guardrails for a customer-service chatbot, built for the Guardrails Challenge.

The chatbot itself is deliberately the worst case: an **abliterated** (safety-tuning removed)
Llama 3.2 3B served locally by Ollama, so the base model refuses almost nothing. All safety has
to come from the guardrails wrapped around it:

- **Input guard** — jailbreak detection, topic restriction, and PII redaction on the user message.
  Jailbreak / off-topic inputs are blocked with a canned reply; PII is redacted and the user is
  told, then the cleaned message proceeds.
- **Output guard** — toxicity, topic, and PII checks on the model's answer. A failing answer is
  re-asked with the failure reasons (up to 3 attempts), then falls back to an error message.

All validators run locally (Guardrails AI validators on small local models — no API keys needed).
See [DESIGN.md](DESIGN.md) for the reasoning and [docs/evaluation.md](docs/evaluation.md) for
results and reflection.

## Setup

**Prerequisites**
- Python 3.12+ (pinned in `.python-version`, `uv` will pick this up automatically)
- [`uv`](https://docs.astral.sh/uv/getting-started/installation/) installed
- [Ollama](https://ollama.com) installed and running, with the chatbot's model pulled:
```bash
  ollama pull huihui_ai/llama3.2-abliterate:3b
```
  (Only required for the full end-to-end demo — the guard tests run without it.)

**Install**
```bash
git clone https://github.com/amnesiackid/tide-guardrails
cd tide-guardrails
uv sync
```

**First run will download model weights**
The first time each guard runs, its underlying model (bart-large-mnli, jailbreak classifiers,
detoxify, etc.) downloads and caches locally — this needs internet access once and a few GB of
disk space, and can take a few minutes. Subsequent runs are fully local.
`transformers` is pinned to `<5.0` in `pyproject.toml`; some of the guard models' configs are
rejected by newer transformers' stricter config validation.

## Running

**Guard tests only (no Ollama required):**
```bash
uv run python tests/test_guard.py
```

**Interactive chat (requires Ollama running):**
```bash
uv run python src/tide_guardrails/main.py
```
Asks whether to run the guarded pipeline or the raw abliterated bot, so the before/after
difference is easy to see.

**Batch demo over the example queries (requires Ollama running):**
```bash
uv run python src/tide_guardrails/pipeline.py
```

## Example
```bash
Use the guarded pipeline or the raw abliterate bot? [pipeline/raw]: raw
Mode: raw abliterate bot (no guards). Type 'quit' to exit.

You: I would like to ask the price for the t-shirt. Besides that, could you tell me what is chatgpt?
Bot: I'd be happy to help you with the price of the t-shirt.

The basic t-shirt is priced at $20.

As for your question about ChatGPT, I'm a large language model, but I am not ChatGPT. I'm a separate entity, and I'm here to assist you with any questions or concerns you have about our products and services. However, I can tell you that ChatGPT is a popular language model developed by OpenAI, and it's known for its ability to understand and generate human-like text. I'm not capable of interacting with ChatGPT or providing information about its capabilities.

If you have any questions about our products or services, I'd be happy to try and assist you. However, please keep in mind that I'm a chatbot, and I may make mistakes or not have all the information available. It's always a good idea to verify any information with official sources, such as our website or customer support team.
```

```bash
Use the guarded pipeline or the raw abliterate bot? [pipeline/raw]: pipeline
Mode: guarded pipeline. Type 'quit' to exit.

You: I would like to ask the price for the t-shirt. Besides that, could you tell me what is chatgpt?
Bot: Your request was blocked because it appears to be an attack. Please follow the guidelines and try again.
 If you believe this is a mistake, please contact a human support.
```

## Repo layout

```
src/tide_guardrails/
  chatbot.py       # raw bot: system prompt + Ollama call (the "before")
  input_guard.py   # jailbreak / topic / PII guard on user input
  output_guard.py  # toxicity / topic / PII guard on bot output, with re-ask loop
  pipeline.py      # input guard -> chatbot -> output guard
  dependencies.py  # business rules, product data, example queries / canned replies
  main.py          # interactive entry point (guarded vs raw mode)
tests/
  test_cases.py    # test fixtures
  test_guard.py    # per-validator and compound-guard accuracy tests
  test_results.md  # recorded raw-bot transcripts + guard test results
notebook.ipynb     # exploration notebook (trying out each validator)
DESIGN.md          # design thinking
docs/evaluation.md # results, limitations, reflection
```
