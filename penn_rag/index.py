"""Embed the passages and store them in a local Chroma database.

    python -m penn_rag.passages     # work/rag/passages.jsonl
    python -m penn_rag.index        # work/rag/chroma/  (rebuilt from scratch)

The section heading is embedded together with the passage text, because a
passage under "PARKING" often never repeats the word. The stored document is
the passage alone. Changing EMBED_MODEL requires a rebuild.
"""
import shutil
from functools import lru_cache

import chromadb
from chromadb.config import Settings

from . import passages
from .config import COLLECTION, DB_DIR, EMBED_MODEL, QUERY_PREFIX

META = ("doc_id", "report", "year", "title", "status", "source", "kind", "section", "page_start", "page_end")


@lru_cache(maxsize=1)
def model():
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(EMBED_MODEL)


def embed(texts: list[str], query: bool = False) -> list[list[float]]:
    if query:
        texts = [QUERY_PREFIX + t for t in texts]
    return model().encode(texts, normalize_embeddings=True, batch_size=32,
                          show_progress_bar=len(texts) > 200).tolist()


def collection(reset: bool = False):
    if reset and DB_DIR.exists():
        shutil.rmtree(DB_DIR)
    client = chromadb.PersistentClient(path=str(DB_DIR), settings=Settings(anonymized_telemetry=False))
    return client.get_or_create_collection(COLLECTION, metadata={"hnsw:space": "cosine"})


def main():
    items = passages.load()
    col = collection(reset=True)
    vectors = embed([f"{p['section']}. {p['text']}" if p["section"] else p["text"] for p in items])
    for i in range(0, len(items), 500):
        part = items[i:i + 500]
        col.add(ids=[p["id"] for p in part], documents=[p["text"] for p in part],
                embeddings=vectors[i:i + 500], metadatas=[{k: p[k] for k in META} for p in part])
    print(f"{col.count()} passages indexed with {EMBED_MODEL} -> {DB_DIR}")


if __name__ == "__main__":
    main()
