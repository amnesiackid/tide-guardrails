"""Indirect prompt injection through retrieved documents (Phase 5).

Builds an index of the real KB plus the documents in tests/poisoned_kb/, then
asks ordinary customer questions and checks whether the answers repeat the
poisoned content. A second part asks benign questions on the clean KB, to check
that the defenses don't cost correct answers. The real cache and
knowledge_base/ are never modified.

Modes:
  raw        RAG bot without any guard (main.py raw mode)
  guarded    Phase 4 pipeline: input guard + output guard, no RAG-specific defenses
  defended   Phase 5 pipeline: + chunk guard, + retrieval-score topic override, + groundedness

Run: uv run python tests/eval_rag_attacks.py [mode ...] [--attacks | --benign]   (requires Ollama)
"""

import os
import sys
import warnings
from pathlib import Path

os.environ["OTEL_SDK_DISABLED"] = "true"
warnings.filterwarnings("ignore")
sys.path.insert(0, str(Path(__file__).parent))

import numpy as np  # noqa: E402

from rag_attack_cases import ATTACK_CASES, BENIGN_CASES, POISONED_KB_DIR  # noqa: E402
from tide_guardrails.chatbot import chatbot_reply  # noqa: E402
from tide_guardrails.pipeline import process_message, retrieve_context, PHASE4, PHASE5  # noqa: E402
from tide_guardrails.rag import retrieval  # noqa: E402
from tide_guardrails.rag.chunking import load_kb  # noqa: E402
from tide_guardrails.rag.embeddings import Index, embed  # noqa: E402

REPO = Path(__file__).resolve().parents[1]
OUT_DIR = Path(__file__).parent

MODES = {
    "raw": lambda q: chatbot_reply(q, retrieve_context(q, defenses=PHASE4)),
    "guarded": lambda q: process_message(q, defenses=PHASE4),
    "defended": lambda q: process_message(q, defenses=PHASE5),
}


def poisoned_index() -> Index:
    base = retrieval.get_index()
    extra = load_kb(REPO / POISONED_KB_DIR)
    vectors = np.vstack([base.vectors, embed([c.embed_text for c in extra])])
    return Index(base.chunks + extra, vectors, fingerprint="poisoned")


def run_attacks(modes: list[str], out) -> None:
    retrieval.set_index_override(poisoned_index())
    try:
        out(f"{len(ATTACK_CASES)} attack cases, modes: {', '.join(modes)}")
        # Is the poisoned chunk even retrieved? (independent of the model)
        out("\nRetrieval: rank of the poisoned chunk in the top 5")
        for case in ATTACK_CASES:
            results = retrieval.retrieve(case["message"], min_score=retrieval.MIN_SCORE)
            ranks = [r for r, (c, _) in enumerate(results, 1) if c.doc_id == case["poison"]]
            out(f"  {case['id']} {case['poison']:15} rank {ranks[0] if ranks else '-'}")

        summary = {m: 0 for m in modes}
        for case in ATTACK_CASES:
            out(f"\n[{case['id']}] ({case['kind']}) {case['message']}")
            for mode in modes:
                answer = MODES[mode](case["message"]).strip()
                hit = [m for m in case["markers"] if m.lower() in answer.lower()]
                summary[mode] += bool(hit)
                verdict = f"ATTACK SUCCEEDED {hit}" if hit else "resisted"
                out(f"  {mode:9} {verdict}\n            {answer[:400].replace(chr(10), ' ')}")

        out("\nAttack success rate (lower is better):")
        for mode in modes:
            out(f"  {mode:9} {summary[mode]}/{len(ATTACK_CASES)}")
    finally:
        retrieval.set_index_override(None)


def run_benign(modes: list[str], out) -> None:
    modes = [m for m in modes if m != "raw"]
    out(f"{len(BENIGN_CASES)} benign questions on the clean KB, modes: {', '.join(modes)}")
    correct = {m: 0 for m in modes}
    for case in BENIGN_CASES:
        out(f"\n[{case['id']}] {case['message']}")
        for mode in modes:
            answer = MODES[mode](case["message"]).strip()
            ok = any(e.lower() in answer.lower() for e in case["expect"])
            correct[mode] += ok
            out(f"  {mode:9} {'correct' if ok else 'WRONG/BLOCKED'}\n"
                f"            {answer[:300].replace(chr(10), ' ')}")
    out("\nBenign answers correct (higher is better):")
    for mode in modes:
        out(f"  {mode:9} {correct[mode]}/{len(BENIGN_CASES)}")


def main(argv: list[str]) -> None:
    modes = [a for a in argv if not a.startswith("--")] or list(MODES)
    parts = {"attacks": run_attacks, "benign": run_benign}
    chosen = [p for p in parts if f"--{p}" in argv] or list(parts)

    for part in chosen:
        lines = []

        def out(s=""):
            print(s, flush=True)
            lines.append(s)

        parts[part](modes, out)
        out_file = OUT_DIR / f"rag_{part}_results.txt"
        out_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"\nSaved to {out_file}\n")


if __name__ == "__main__":
    main(sys.argv[1:])
