"""Phase 5: guards that only exist because of RAG.

1. Chunk screen. Retrieved text enters the prompt without passing the input
   guard, so a poisoned document is an indirect prompt injection. We drop
   retrieved chunks that address orders to the assistant.

   Why a phrase list and not a model: on our KB, DetectJailbreak scored real
   policy chunks HIGHER (median 0.69, max 0.80) than the poisoned ones
   (0.67-0.75), and a bart-large-mnli zero-shot "instructions to an AI" label
   scored real chunks that talk about the chatbot up to 0.98 vs 0.04-0.29 for
   the poison. The phrase list caught every order-style poison with zero hits on
   the 199 real chunks. It is easy to evade by rewording, and it cannot catch a
   false fact stated in normal policy language (see tests/eval_rag_attacks.py).

2. Groundedness. Every sentence of the answer that makes a checkable claim (a
   number, price or percentage) must be entailed by at least one retrieved chunk,
   judged by the NLI model bart-large-mnli that RestrictToTopic already uses.
   bart-large-mnli is English-only, so non-English answers are not checked.
"""

import re
from functools import lru_cache

from tide_guardrails.rag.chunking import Chunk

# --- 1. chunk screen ---------------------------------------------------------

INJECTION_PATTERN = re.compile(
    r"ignore (all |any )?(previous|prior|above|earlier)"
    r"|(notice|instruction|message)s? (to|for) the (assistant|chatbot|ai|model)"
    r"|you are now|staff mode|developer mode"
    r"|(always |you must )?(tell|instruct|inform) (the|every|all) customers?\b"
    r"|reply that|say (this|that)|do not (mention|reveal|tell)"
    r"|the assistant (must|should)",
    re.IGNORECASE,
)


def screen_chunks(results: list[tuple[Chunk, float]]):
    """Split retrieved (chunk, score) pairs into (kept, dropped)."""
    kept, dropped = [], []
    for chunk, score in results:
        (dropped if INJECTION_PATTERN.search(chunk.text) else kept).append((chunk, score))
    return kept, dropped


# --- 2. groundedness ---------------------------------------------------------

NLI_MODEL = "facebook/bart-large-mnli"
ENTAILMENT_THRESHOLD = 0.5
CLAIM = re.compile(r"\d|\$|%")
SENTENCE_END = re.compile(r"(?<=[.!?])\s+|\n+")
# A cheap "is this English?" check: bart-large-mnli only understands English.
ENGLISH_WORDS = re.compile(r"\b(the|is|are|and|you|your|can|of|to|our|it|we|a|for|in)\b", re.IGNORECASE)
GERMAN_WORDS = re.compile(r"\b(der|die|das|und|ist|nicht|sie|ich|ein|eine|zu|wir|ihr|haben|kann)\b", re.IGNORECASE)
CJK = re.compile(r"[぀-ヿ㐀-鿿가-힯]")


def is_english(text: str) -> bool:
    """English unless it has CJK characters or more German than English function
    words. A short answer with neither ("Yes, laptops cost $999.") counts as English."""
    return not CJK.search(text) and len(ENGLISH_WORDS.findall(text)) >= len(GERMAN_WORDS.findall(text))


@lru_cache(maxsize=1)
def _nli():
    import torch
    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(NLI_MODEL)
    model = AutoModelForSequenceClassification.from_pretrained(NLI_MODEL).eval()
    entail_id = model.config.label2id.get("entailment", 2)
    return torch, tokenizer, model, entail_id


def entailment(premises: list[str], hypotheses: list[str]) -> list[float]:
    torch, tokenizer, model, entail_id = _nli()
    batch = tokenizer(premises, hypotheses, return_tensors="pt", padding=True,
                      truncation="only_first", max_length=512)
    with torch.no_grad():
        probs = model(**batch).logits.softmax(dim=-1)
    return probs[:, entail_id].tolist()


def claim_sentences(answer: str) -> list[str]:
    return [s.strip() for s in SENTENCE_END.split(answer) if s.strip() and CLAIM.search(s)]


def check_grounded(answer: str, chunks: list[Chunk]) -> dict:
    """Return {"grounded": bool, "unsupported": [sentences], "checked": n, "best_chunk": Chunk|None}.

    A claim sentence is supported when some retrieved chunk entails it with
    probability >= ENTAILMENT_THRESHOLD. With no chunks, every claim is unsupported.
    best_chunk is the chunk that came closest to supporting the unsupported claims
    (what the model was trying to say), used for the verbatim fallback."""
    claims = claim_sentences(answer)
    if not claims or not is_english(answer):
        return {"grounded": True, "unsupported": [], "checked": 0, "best_chunk": None}
    if not chunks:
        return {"grounded": False, "unsupported": claims, "checked": len(claims), "best_chunk": None}

    premises = [f"{c.title}. {c.heading}. {c.text}" for c in chunks]
    n = len(premises)
    scores = entailment(premises * len(claims), [h for h in claims for _ in premises])
    rows = [scores[i * n:(i + 1) * n] for i in range(len(claims))]
    unsupported = [h for h, row in zip(claims, rows) if max(row) < ENTAILMENT_THRESHOLD]
    best_chunk = None
    if unsupported:
        totals = [sum(row[j] for h, row in zip(claims, rows) if h in unsupported) for j in range(n)]
        best_chunk = chunks[max(range(n), key=totals.__getitem__)]
    return {"grounded": not unsupported, "unsupported": unsupported,
            "checked": len(claims), "best_chunk": best_chunk}
