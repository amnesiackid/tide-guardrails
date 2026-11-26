"""Phase 3: retrieve the top-k chunks for a query by cosine similarity.

Vectors are L2-normalized (see embeddings.py), so cosine similarity is a dot
product: one (n_chunks, dim) @ (dim,) multiply scores the query against every
chunk. At ~200 chunks plain numpy is instant; a vector DB only starts to pay
off at a scale or with features (filters, persistence, ANN) we don't need yet.
"""

from functools import lru_cache

import numpy as np

from tide_guardrails.rag.chunking import Chunk
from tide_guardrails.rag.embeddings import Index, embed, load_or_build_index

DEFAULT_STRATEGY = "section"
DEFAULT_K = 5          # k=3 misses "problem with product X" questions whose policy ranks 4th-5th
MIN_SCORE = 0.50       # top-1 below this: treat as "the KB has no answer" (see tests/retrieval_results.txt)


_override: Index | None = None


def set_index_override(index: Index | None) -> None:
    """Make every retrieval use `index` (None restores the normal KB index).
    Used by tests/eval_rag_attacks.py to add poisoned documents without
    touching knowledge_base/ or the cache."""
    global _override
    _override = index


@lru_cache(maxsize=2)
def _load_index(product_strategy: str) -> Index:
    return load_or_build_index(product_strategy, verbose=False)


def get_index(product_strategy: str = DEFAULT_STRATEGY) -> Index:
    return _override if _override is not None else _load_index(product_strategy)


def rank(scores: np.ndarray, index: Index, k: int) -> list[tuple[Chunk, float]]:
    top = np.argsort(-scores)[:k]
    return [(index.chunks[i], float(scores[i])) for i in top]


def retrieve(
    query: str,
    k: int = DEFAULT_K,
    product_strategy: str = DEFAULT_STRATEGY,
    min_score: float | None = None,
) -> list[tuple[Chunk, float]]:
    """Return up to k (chunk, cosine score) pairs, best first.

    min_score drops chunks below a similarity threshold, so a query with no good
    match can return an empty list instead of the "least bad" chunks.
    """
    index = get_index(product_strategy)
    scores = index.vectors @ embed([query])[0]
    results = rank(scores, index, k)
    if min_score is not None:
        results = [(c, s) for c, s in results if s >= min_score]
    return results


def retrieve_batch(
    queries: list[str], k: int = 5, product_strategy: str = DEFAULT_STRATEGY
) -> list[list[tuple[Chunk, float]]]:
    """Same as retrieve() for many queries with one embedding call (used by the evaluation)."""
    index = get_index(product_strategy)
    scores = embed(queries) @ index.vectors.T      # (n_queries, n_chunks)
    return [rank(row, index, k) for row in scores]


if __name__ == "__main__":
    import sys

    query = " ".join(sys.argv[1:]) or "Can I return a shirt I wore once?"
    print(f"Q: {query}")
    for c, s in retrieve(query):
        print(f"  {s:.3f}  {c.chunk_id:30} {c.title} > {c.heading}")
