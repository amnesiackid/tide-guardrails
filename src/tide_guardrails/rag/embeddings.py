"""Phase 2: turn chunks into vectors with bge-m3 (via Ollama) and cache them on disk.

An embedding maps a text to a point in a 1024-dimensional space where texts with
similar meaning land close together. We L2-normalize every vector, so the cosine
similarity between two texts is just their dot product: 1.0 = same direction,
~0 = unrelated. bge-m3 is multilingual, so a German or Chinese question lands
near the English chunk that answers it.

Embedding is the slow, repeated step, so the index is cached. The cache key is a
fingerprint of the model, the chunking strategy and every chunk's id and text;
if any of those change, the index is rebuilt, otherwise it is loaded from disk.
"""

import hashlib
import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import requests

from tide_guardrails.rag.chunking import Chunk, load_kb

OLLAMA_URL = "http://localhost:11434/api/embed"
EMBED_MODEL = "bge-m3"
REPO_ROOT = Path(__file__).resolve().parents[3]
KB_DIR = REPO_ROOT / "knowledge_base"
CACHE_DIR = REPO_ROOT / ".rag_cache"


def embed(texts: list[str], batch_size: int = 32) -> np.ndarray:
    """Embed texts with bge-m3. Returns a float32 array (len(texts), dim), rows L2-normalized."""
    vectors = []
    for start in range(0, len(texts), batch_size):
        batch = texts[start:start + batch_size]
        try:
            response = requests.post(
                OLLAMA_URL,
                json={"model": EMBED_MODEL, "input": batch},
                timeout=300,
            )
            response.raise_for_status()
        except requests.RequestException as e:
            raise RuntimeError(
                f"Embedding failed ({e}). Is Ollama running, and did you `ollama pull {EMBED_MODEL}`?"
            ) from e
        vectors.extend(response.json()["embeddings"])

    matrix = np.asarray(vectors, dtype=np.float32)
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    return matrix / np.clip(norms, 1e-12, None)


@dataclass
class Index:
    chunks: list[Chunk]
    vectors: np.ndarray      # (n_chunks, dim), row i belongs to chunks[i]
    fingerprint: str


def fingerprint(chunks: list[Chunk], product_strategy: str) -> str:
    h = hashlib.sha256()
    h.update(f"{EMBED_MODEL}|{product_strategy}".encode())
    for c in chunks:
        h.update(f"\x00{c.chunk_id}\x00{c.embed_text}".encode("utf-8"))
    return h.hexdigest()


def load_or_build_index(
    product_strategy: str = "section",
    kb_dir: Path = KB_DIR,
    cache_dir: Path = CACHE_DIR,
    force: bool = False,
    verbose: bool = True,
) -> Index:
    """Chunk the KB, then load cached vectors if the KB is unchanged, else re-embed and save."""
    chunks = load_kb(kb_dir, product_strategy)
    fp = fingerprint(chunks, product_strategy)
    cache_file = cache_dir / f"index-{product_strategy}.npz"

    if cache_file.exists() and not force:
        cached = np.load(cache_file, allow_pickle=False)
        if str(cached["fingerprint"]) == fp:
            if verbose:
                print(f"[index] loaded {len(chunks)} vectors from {cache_file.name} (KB unchanged)")
            return Index(chunks, cached["vectors"], fp)
        if verbose:
            print("[index] KB or settings changed, rebuilding")

    t0 = time.perf_counter()
    vectors = embed([c.embed_text for c in chunks])
    cache_dir.mkdir(parents=True, exist_ok=True)
    np.savez(
        cache_file,
        vectors=vectors,
        fingerprint=np.array(fp),
        chunk_ids=np.array([c.chunk_id for c in chunks]),
    )
    if verbose:
        print(f"[index] embedded {len(chunks)} chunks in {time.perf_counter() - t0:.1f}s "
              f"-> {cache_file.name}")
    return Index(chunks, vectors, fp)


if __name__ == "__main__":
    for strategy in ("section", "whole"):
        t0 = time.perf_counter()
        index = load_or_build_index(strategy)
        print(f"  shape={index.vectors.shape}  "
              f"norms≈{np.linalg.norm(index.vectors, axis=1).mean():.3f}  "
              f"({time.perf_counter() - t0:.2f}s)")

    # Sanity check, not retrieval yet: the nearest chunks for a few questions should make sense.
    index = load_or_build_index("section", verbose=False)
    queries = [
        "Can I return a shirt I wore once?",
        "Wie lange dauert der Versand nach Deutschland?",   # German: shipping time to Germany
        "耳机的电池能用多久？",                                 # Chinese: earbuds battery life
    ]
    scores = embed(queries) @ index.vectors.T                # cosine similarity, (n_queries, n_chunks)
    for q, row in zip(queries, scores):
        print(f"\nQ: {q}")
        for i in np.argsort(-row)[:3]:
            c = index.chunks[i]
            print(f"  {row[i]:.3f}  {c.chunk_id:22} {c.title} > {c.heading}")
