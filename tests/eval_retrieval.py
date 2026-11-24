"""Retrieval evaluation (Phase 3): hit@k and MRR per chunking strategy, no LLM involved.

Retrieval is measured on its own because a wrong answer can come from two places:
the right chunk was never retrieved, or it was retrieved and the model ignored it.
This script only measures the first, the same way tests/test_guard.py scores each
validator on its own before scoring the compound guard.

  hit@k  share of answerable questions with a chunk from an expected doc in the top k
  MRR    mean of 1/rank of the first such chunk (0 if not in the top 10)

No-answer questions can't be "hit"; for them we look at the top-1 score instead,
and ask whether a score threshold could tell them apart from answerable questions.

Run: uv run python tests/eval_retrieval.py   (requires Ollama with bge-m3)
"""

import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from rag_questions import QUESTIONS  # noqa: E402
from tide_guardrails.rag.retrieval import retrieve_batch  # noqa: E402

K_MAX = 10
STRATEGIES = ("section", "whole")
OUT_FILE = Path(__file__).parent / "retrieval_results.txt"

lines: list[str] = []


def out(s: str = "") -> None:
    print(s)
    lines.append(s)


def first_hit_rank(results, expected: list[str]) -> int | None:
    for r, (chunk, _) in enumerate(results, 1):
        if chunk.doc_id in expected:
            return r
    return None


def evaluate(strategy: str) -> dict:
    all_results = retrieve_batch([q["query"] for q in QUESTIONS], k=K_MAX, product_strategy=strategy)
    rows = []
    for q, results in zip(QUESTIONS, all_results):
        rows.append({**q, "results": results,
                     "rank": first_hit_rank(results, q["expected"]) if q["expected"] else None,
                     "top1": results[0][1]})
    return {"strategy": strategy, "rows": rows}


def metrics(rows) -> dict:
    n = len(rows)
    ranks = [r["rank"] for r in rows]
    return {
        "n": n,
        "hit@1": sum(1 for x in ranks if x and x <= 1) / n,
        "hit@3": sum(1 for x in ranks if x and x <= 3) / n,
        "hit@5": sum(1 for x in ranks if x and x <= 5) / n,
        "mrr": sum(1 / x for x in ranks if x) / n,
    }


def fmt(m: dict) -> str:
    return f"{m['n']:3}  {m['hit@1']:6.0%} {m['hit@3']:6.0%} {m['hit@5']:6.0%}  {m['mrr']:.3f}"


def report(ev: dict) -> None:
    rows = ev["rows"]
    answerable = [r for r in rows if r["expected"]]
    no_answer = [r for r in rows if not r["expected"]]

    out(f"\n{'=' * 72}\nStrategy: {ev['strategy']}\n{'=' * 72}")
    out(f"{'group':16}   n   hit@1  hit@3  hit@5  MRR")
    out(f"{'ALL answerable':16} {fmt(metrics(answerable))}")
    by_kind = defaultdict(list)
    for r in answerable:
        by_kind[r["kind"]].append(r)
    for kind, group in by_kind.items():
        out(f"  {kind:14} {fmt(metrics(group))}")
    by_lang = defaultdict(list)
    for r in answerable:
        by_lang[r["lang"]].append(r)
    for lang, group in sorted(by_lang.items()):
        out(f"  lang={lang:9} {fmt(metrics(group))}")

    out("\nMisses at k=3 (expected doc not in the top 3):")
    for r in answerable:
        if not r["rank"] or r["rank"] > 3:
            out(f"  {r['id']} [{r['kind']}] {r['query']}")
            out(f"       expected {r['expected']}, first hit at rank {r['rank'] or '>10'}")
            for c, s in r["results"][:3]:
                out(f"       {s:.3f} {c.chunk_id:28} {c.title} > {c.heading}")

    # Can a top-1 score threshold separate answerable from no-answer questions?
    pos = sorted(r["top1"] for r in answerable)
    neg = sorted(r["top1"] for r in no_answer)
    out("\nTop-1 score, answerable vs no-answer:")
    out(f"  answerable  min {pos[0]:.3f}  median {pos[len(pos) // 2]:.3f}  max {pos[-1]:.3f}")
    out(f"  no-answer   min {neg[0]:.3f}  median {neg[len(neg) // 2]:.3f}  max {neg[-1]:.3f}")
    for r in no_answer:
        c, s = r["results"][0]
        out(f"    {r['id']} {s:.3f} {r['query'][:40]:40} -> {c.title} > {c.heading}")
    best = max(
        (sum(p >= t for p in pos) + sum(n < t for n in neg), t)
        for t in [x / 100 for x in range(30, 80)]
    )
    out(f"  best threshold {best[1]:.2f}: {best[0]}/{len(pos) + len(neg)} classified correctly "
        f"({sum(p < best[1] for p in pos)} answerable wrongly rejected, "
        f"{sum(n >= best[1] for n in neg)} no-answer let through)")


if __name__ == "__main__":
    n_ans = sum(1 for q in QUESTIONS if q["expected"])
    out(f"{len(QUESTIONS)} questions ({n_ans} answerable, {len(QUESTIONS) - n_ans} no-answer)")
    evals = [evaluate(s) for s in STRATEGIES]
    for ev in evals:
        report(ev)

    out(f"\n{'=' * 72}\nSummary (answerable questions)\n{'=' * 72}")
    out(f"{'strategy':16}   n   hit@1  hit@3  hit@5  MRR")
    for ev in evals:
        out(f"{ev['strategy']:16} {fmt(metrics([r for r in ev['rows'] if r['expected']]))}")

    OUT_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nSaved to {OUT_FILE}")
