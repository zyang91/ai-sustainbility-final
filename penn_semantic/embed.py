"""Embed the corpus passages for the semantic analysis.

    python -m penn_semantic.embed

Units are the retrieval passages of Part 2 (work/rag/passages.jsonl): prose
only, about 1,000 characters each, second scans of a plan left out. Tables
are left out here: their text is figures and row labels, which a sentence
model does not read as language. Each passage is embedded on its own text,
without its section heading, so that a heading does not decide its theme.

Model: BAAI/bge-base-en-v1.5 through sentence-transformers, the same model as
retrieval, so the analysis and the chatbot see the corpus the same way.
Vectors are L2-normalised; cosine similarity is a dot product.

Writes work/semantic/passages.jsonl (metadata) and work/semantic/vectors.npy.
"""
import json

import numpy as np

from penn_ocr.config import WORK
from penn_rag import passages
from penn_rag.config import EMBED_MODEL, QUERY_PREFIX

OUT = WORK / "semantic"
META = OUT / "passages.jsonl"
VECTORS = OUT / "vectors.npy"

# Plan eras used for temporal comparison. The archive has no plans for
# 1949-1960 or 1967-1976, so these are the periods the documents fall into.
ERAS = [("1948", 1948, 1948), ("1960s", 1961, 1966), ("Late 1970s", 1977, 1979),
        ("1980s", 1982, 1987), ("1990s", 1992, 1998), ("2006-2018", 2006, 2018)]


def era(year: int) -> str:
    return next(name for name, a, b in ERAS if a <= year <= b)


_model = None


def model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer(EMBED_MODEL)
    return _model


def encode(texts: list[str], query: bool = False) -> np.ndarray:
    if query:
        texts = [QUERY_PREFIX + t for t in texts]
    return model().encode(texts, normalize_embeddings=True, batch_size=32,
                          show_progress_bar=len(texts) > 200)


def load() -> tuple[list[dict], np.ndarray]:
    with open(META) as f:
        return [json.loads(line) for line in f], np.load(VECTORS)


def main():
    items = [p for p in passages.load() if p["kind"] == "text"]
    OUT.mkdir(parents=True, exist_ok=True)
    vecs = encode([p["text"] for p in items])
    with open(META, "w") as f:
        for p in items:
            f.write(json.dumps(dict({k: p[k] for k in ("id", "doc_id", "report", "year", "title", "status",
                                                        "section", "page_start", "page_end", "text")},
                                    era=era(p["year"])), ensure_ascii=False) + "\n")
    np.save(VECTORS, vecs.astype(np.float32))
    print(f"{len(items)} passages, {vecs.shape[1]} dimensions -> {VECTORS}")


if __name__ == "__main__":
    main()
