"""Find the passages closest in meaning to a question.

    python -m penn_rag.retrieve "How was parking handled in the 1960s?"
    python -m penn_rag.retrieve "pedestrian walks" --from 1975 --to 1985

`search` returns the best passages overall. `search_by_report` returns the
best few from every report in range, so a question that compares periods is
not answered from the two longest documents alone.
"""
import argparse

from . import index
from .config import PER_REPORT, TOP_K


def _where(year_from=None, year_to=None, status=None, report=None) -> dict | None:
    conds = []
    if year_from:
        conds.append({"year": {"$gte": int(year_from)}})
    if year_to:
        conds.append({"year": {"$lte": int(year_to)}})
    if status in ("final", "draft"):
        conds.append({"status": status})
    if report:
        conds.append({"report": report})
    return None if not conds else conds[0] if len(conds) == 1 else {"$and": conds}


def _hits(res) -> list[dict]:
    return [dict(meta, id=i, text=doc, score=round(1 - dist, 3))
            for i, doc, meta, dist in zip(res["ids"][0], res["documents"][0],
                                          res["metadatas"][0], res["distances"][0])]


def search(question: str, k: int = TOP_K, **filters) -> list[dict]:
    col = index.collection()
    res = col.query(query_embeddings=index.embed([question], query=True), n_results=k,
                    where=_where(**filters))
    return _hits(res)


def search_by_report(question: str, per_report: int = PER_REPORT, pool: int = 80, **filters) -> list[dict]:
    """The best `per_report` passages of each report, reports in date order."""
    out, seen = [], {}
    for h in search(question, k=pool, **filters):
        if seen.get(h["report"], 0) < per_report:
            seen[h["report"]] = seen.get(h["report"], 0) + 1
            out.append(h)
    return sorted(out, key=lambda h: (h["year"], h["report"], -h["score"]))


def plan_years() -> str:
    """"1948, 1961, ..." for the prompt, so the model knows which years exist."""
    from . import passages
    return ", ".join(str(y) for y in sorted({p["year"] for p in passages.load()}))


def missing_names(question: str, hits: list[dict]) -> list[str]:
    """Capitalised names in the question that occur in none of the passages.

    Similarity scores do not tell an off-topic question from an on-topic one
    (a search for a place the plans never mention still scores about 0.63),
    so this literal check is passed to the model as a fact.
    """
    import re
    # the plan's own title and section heading count: "Master Land Use Plan" is how a
    # question names the document, and it is rarely repeated in the body text
    text = " ".join(f"{h['text']} {h['title']} {h['section']}" for h in hits).lower()
    words = re.findall(r"(?<![.?!]\s)(?<!^)\b[A-Z][a-z]{3,}\b", question)
    return sorted({w for w in words if w.lower() not in text})


def cite(h: dict) -> str:
    pages = f"p. {h['page_start']}" if h["page_start"] == h["page_end"] \
        else f"pp. {h['page_start']}-{h['page_end']}"
    return f"{h['title']} ({h['year']}, {h['status']}), {pages}" + (", table" if h.get("kind") == "table" else "")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("question")
    ap.add_argument("--from", dest="year_from", type=int)
    ap.add_argument("--to", dest="year_to", type=int)
    ap.add_argument("--status", choices=["final", "draft"])
    ap.add_argument("--by-report", action="store_true")
    a = ap.parse_args()
    f = dict(year_from=a.year_from, year_to=a.year_to, status=a.status)
    for h in (search_by_report(a.question, **f) if a.by_report else search(a.question, **f)):
        print(f"{h['score']:.3f}  {cite(h)}  [{h['section']}]\n       {h['text'][:230]}\n")
