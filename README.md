## Setup

**Prerequisites**
- Python 3.12+ (pinned in `.python-version`, `uv` will pick this up automatically)
- [`uv`](https://docs.astral.sh/uv/getting-started/installation/) installed
- [Ollama](https://ollama.com) installed and running, with the chatbot's model pulled:
```bash
  ollama pull huihui_ai/llama3.2-abliterate:3b
```
  (Only required for the full end-to-end demo — see "Running" below.)

**Install**
```bash
git clone https://github.com/amnesiackid/tide-guardrails
cd tide-guardrails
uv sync
```

**Known manual fix required (not automated by `uv sync`)**
[Describe here exactly what you changed in which installed package's `config.json` and why —
e.g. "transformers' strict config validation rejects <model>'s string-valued id2label field;
edit `.venv/lib/.../config.json`, changing `id2label` from `{...}` to `{...}`."]

**First run will download model weights**
The first time each guard runs, its underlying model (bart-large-mnli, detoxify, etc.) downloads
and caches locally — this needs internet access once and a few GB of disk space, and can take a
few minutes. Subsequent runs are fully local.

## Running

**Guard tests only (no Ollama required):**
```bash
uv run python tests/test.py
```

**Full chatbot pipeline (requires Ollama running):**
```bash
uv run python src/guardrails/pipepline.py
```