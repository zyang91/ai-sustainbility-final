"""Page-level review of the full-corpus OCR (after `page_ocr --all`).

The corpus builder drops text that the layout model filed under a figure, and
some pages come out with almost no text. Most of those pages are maps,
drawings or dividers, but some are body text the layout model mislabelled.
This module lists the pages worth a look; a person decides from the page
image in `app/page_review.py`.

Every decision is appended to `annotation/page_checks.jsonl`. The latest
record per page wins, and `penn_ocr.corpus` applies it.
"""
import json
from datetime import datetime, timezone

from .config import PAGE_CHECKS, PAGE_OCR

VERDICTS = {
    "keep": "Keep everything (green + red)",
    "figure": "Keep green only (as it is now)",
    "drop": "Delete all text from this page",
    "redo": "Printed text has no box: OCR missed it",
}
# why a page is in the queue, most suspicious first
REASONS = {
    "dropped": "OCR read text that the corpus left out",
    "lowconf": "Low recognition confidence",
    "little": "Little text kept",
    "empty": "Almost no text found",
}
THIN = 100           # characters; fewer than this on a page counts as "little"
DROPPED = 300        # characters left out before a page counts as "dropped"
LOW_CONF = 0.85


def record(doc_id: str, page: int, verdict: str, reason: str = "", note: str = "",
           annotator: str = "", handwriting: bool = False) -> None:
    """Append one decision. An empty verdict reopens the page."""
    rec = dict(doc_id=doc_id, page=page, verdict=verdict, reason=reason, note=note.strip(),
               handwriting=handwriting, annotator=annotator.strip(),
               saved_at=datetime.now(timezone.utc).isoformat(timespec="seconds"))
    PAGE_CHECKS.parent.mkdir(exist_ok=True)
    with open(PAGE_CHECKS, "a") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def latest() -> dict[tuple[str, int], dict]:
    out = {}
    if PAGE_CHECKS.exists():
        with open(PAGE_CHECKS) as f:
            for line in f:
                if line.strip():
                    rec = json.loads(line)
                    out[(rec["doc_id"], rec["page"])] = rec
    return {k: r for k, r in out.items() if r["verdict"]}


def verdicts() -> dict[tuple[str, int], str]:
    return {k: r["verdict"] for k, r in latest().items()}


def split(page: dict) -> tuple[list[dict], list[dict]]:
    """(lines the corpus keeps by default, lines it leaves out) for one page."""
    from .corpus import SKIP_LABELS, assign
    kept, left_out = [], []
    for b in assign(page):
        (left_out if b["label"] in SKIP_LABELS else kept).extend(b["lines"])
    return kept, left_out


def _chars(lines: list[dict]) -> int:
    return sum(len(l["text"]) for l in lines)


def candidates(docs: list[dict]) -> list[dict]:
    """Pages worth a look, most suspicious reason first, then by document."""
    out = []
    for d in docs:
        for f in sorted((PAGE_OCR / d["doc_id"]).glob("p*.json")):
            page = json.loads(f.read_text())
            if page["page"] < d["first_content_page"]:
                continue
            kept, left_out = split(page)
            n_kept, n_out = _chars(kept), _chars(left_out)
            total = n_kept + n_out
            conf = sum(l["score"] * len(l["text"]) for l in page["lines"]) / total if total else 0
            if n_out >= DROPPED and n_kept < 0.6 * total:
                reason = "dropped"
            elif total < THIN:
                reason = "empty"
            elif n_kept < THIN:
                reason = "little"
            elif conf < LOW_CONF:
                reason = "lowconf"
            else:
                continue
            out.append(dict(doc_id=d["doc_id"], page=page["page"], reason=reason,
                            kept_chars=n_kept, left_out_chars=n_out, confidence=round(conf, 3)))
    order = list(REASONS)
    out.sort(key=lambda c: (order.index(c["reason"]), -c["left_out_chars"] if c["reason"] == "dropped" else 0,
                            c["doc_id"], c["page"]))
    return out
