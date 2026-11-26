from dataclasses import dataclass, field
from pathlib import Path
from random import sample
from statistics import median

import yaml


@dataclass
class Doc:
    id: str
    title: str
    type: str          # "product" | "policy" | "faq"
    category: str
    body: str          # markdown after the frontmatter
    source: Path
    metadata: dict = field(default_factory=dict)   # sku, price_usd, in_stock, ...


@dataclass
class Chunk:
    doc_id: str
    title: str
    type: str
    category: str
    chunk_id: str    
    heading: str
    text: str
    source: Path
    
    
    @property
    def embed_text(self) -> str:
        return f"{self.title} > {self.heading}\n{self.text}"


def load_doc(path: Path) -> Doc:
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
        if not content.startswith("---"):
            raise ValueError(f"no frontmatter: {path}")
        parts = content.split("---", 2)
        
        meta = yaml.safe_load(parts[1])        # the YAML block
        doc_id = meta.pop("id")
        doc_title = meta.pop("title")
        doc_type = meta.pop("type")
        doc_category = meta.pop("category")
        text = parts[2].strip() if len(parts) > 2 else ""

        return Doc(
            id=doc_id,
            title=doc_title,
            type=doc_type,
            category=doc_category,
            body=text,
            source=path,
            metadata=meta
        )


def chunk(doc: Doc, product_strategy: str = "section") -> list[Chunk]:
    # product_strategy can be "section" (default) or "whole"
    # TODO: walk doc.body line by line; a line starting with "## " starts a new
    #       section; text before the first "## " becomes the "Overview" chunk
    is_product = doc.type == "product"
    if product_strategy == "whole" and is_product:
        return [
            Chunk(
                type=doc.type,
                category=doc.category,
                doc_id=doc.id,
                chunk_id=f"{doc.id}-1",
                title=doc.title,
                heading="Full Document",
                text=doc.body,
                source=doc.source
            )
        ]
    else:
            
        lines = doc.body.splitlines()        # str -> list of lines, without the '\n'
        sections = []
        heading, buf = "Overview", []
        for line in lines:
            if line.startswith("# "):
                continue              # skip the document title
            if line.startswith("## "):
                sections.append((heading, "\n".join(buf).strip()))
                heading, buf = line[3:].strip(), []
            else:
                buf.append(line)
        sections.append((heading, "\n".join(buf).strip()))
        return [
            Chunk(
                type=doc.type,
                category=doc.category,
                doc_id=doc.id,
                chunk_id=f"{doc.id}-{i}",
                title=doc.title,
                heading=heading,
                text=text,
                source=doc.source
            )
            for i, (heading, text) in enumerate(sections, 1) if text.strip() != ""
        ]

def load_kb(kb: Path = Path("knowledge_base"), product_strategy: str = "section") -> list[Chunk]:
    docs = [load_doc(path) for path in sorted(kb.glob("**/*.md"))]
    return [c for d in docs for c in chunk(d, product_strategy)]


if __name__ == "__main__":
    kb = Path("knowledge_base")
    docs = [load_doc(path) for path in sorted(kb.glob("**/*.md"))]
    for strategy in ("section", "whole"):
        chunks = [c for d in docs for c in chunk(d, strategy)]
        print(f"\n[{strategy}] {len(docs)} docs -> {len(chunks)} chunks")
        for t in ("product", "policy", "faq"):
            words = sorted(len(c.embed_text.split()) for c in chunks if c.type == t)
            if words:
                print(f"  {t:8} n={len(words):3}  words min/median/max = "
                      f"{words[0]}/{median(words):.0f}/{words[-1]}")

    ids = [c.chunk_id for c in chunks]
    assert len(ids) == len(set(ids)), "duplicate chunk_ids"

    print("\n--- 5 random chunks (section strategy) ---")
    for c in sample([c for d in docs for c in chunk(d)], 5):
        print(f"\n[{c.chunk_id}]\n{c.embed_text}")