"""Cut the corpus into retrievable passages.

    python -m penn_rag.passages

Input: work/corpus/paragraphs.jsonl. Only prose blocks are used, and second
scans of the same plan are skipped. Neighbouring blocks of one report are
joined until a passage reaches about PASSAGE_CHARS characters, so a sentence
that the page layout or the PDF split into fragments is whole again. A
section heading starts a new passage and is kept as metadata. Every passage
records the source PDF and the pages it came from, for citation.

Tables are not prose, but they hold the figures that planning questions ask
for (parking spaces, floor area, enrolment). Each table becomes a passage of
its own, rows kept on separate lines, with the caption printed above it.
"""
import json
import re

from .config import PARAGRAPHS, PASSAGE_CHARS, PASSAGE_MAX, PASSAGES

HEADINGS = {"paragraph_title", "doc_title"}
SECTION_PAGES = 2     # a heading stops applying this many pages on (the next one may have been missed)


def split_long(text: str) -> list[str]:
    """Pieces of at most PASSAGE_MAX characters, cut at sentence ends."""
    if len(text) <= PASSAGE_MAX:
        return [text]
    out, cur = [], ""
    for sent in re.split(r"(?<=[.;:?!])\s+", text):
        if cur and len(cur) + len(sent) + 1 > PASSAGE_CHARS:
            out.append(cur)
            cur = sent
        else:
            cur = f"{cur} {sent}" if cur else sent
    return out + [cur] if cur else out


def build(rows: list[dict]) -> list[dict]:
    out, cur, section, section_page = [], None, "", 0
    caption, table = [], None      # short lines just above a table; the table being built

    def flush():
        nonlocal cur
        if cur:
            cur["text"] = " ".join(cur.pop("parts"))
            out.append(cur)
        cur = None

    for r in rows:
        if r["duplicate_of"]:
            continue
        if cur and r["doc_id"] != cur["doc_id"]:
            flush()
            section = ""
        if r["label"] == "table":
            flush()
            if table and (table["doc_id"], table["page_end"]) == (r["doc_id"], r["page"]):
                table["parts"] += r["lines"]            # the layout model cut one table in two
            else:
                table = dict(doc_id=r["doc_id"], report=r["report"], year=r["year"], title=r["title"],
                             status=r["status"], source=r["source"], kind="table",
                             section=" ".join(caption[-2:]) or section,
                             page_start=r["page"], page_end=r["page"], parts=list(r["lines"]), chars=0)
                out.append(table)
            caption = []
            continue
        if not r["prose"] and len(r["text"]) < 120 and re.search(r"[A-Za-z]{3}", r["text"]):
            caption.append(r["text"])
        elif r["prose"]:
            caption, table = [], None
        if r["label"] in HEADINGS and len(r["text"]) < 120:
            flush()
            section, section_page = r["text"], r["page"]
            continue
        if not r["prose"]:
            continue
        if section and r["page"] > section_page + SECTION_PAGES:
            flush()
            section = ""
        for piece in split_long(r["text"]):
            if cur and cur["chars"] + len(piece) > PASSAGE_MAX:
                flush()
            if cur is None:
                cur = dict(kind="text", doc_id=r["doc_id"], report=r["report"], year=r["year"], title=r["title"],
                           status=r["status"], source=r["source"], section=section,
                           page_start=r["page"], page_end=r["page"], parts=[], chars=0)
            cur["parts"].append(piece)
            cur["chars"] += len(piece) + 1
            cur["page_end"] = r["page"]
            if cur["chars"] >= PASSAGE_CHARS:
                flush()
    flush()
    for p in out:
        if p["kind"] == "table":
            p["text"] = "\n".join(p.pop("parts"))[:PASSAGE_MAX * 2]
            p["chars"] = len(p["text"])
    out = [p for p in out if p["kind"] == "text" or sum(c.isdigit() for c in p["text"]) >= 6]
    for i, p in enumerate(out):
        p["id"] = f"{p['doc_id']}-p{p['page_start']:04d}-{i:05d}"
    return out


def load() -> list[dict]:
    with open(PASSAGES) as f:
        return [json.loads(line) for line in f]


def main():
    with open(PARAGRAPHS) as f:
        rows = [json.loads(line) for line in f]
    passages = build(rows)
    PASSAGES.parent.mkdir(parents=True, exist_ok=True)
    with open(PASSAGES, "w") as f:
        for p in passages:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")
    lengths = sorted(p["chars"] for p in passages)
    print(f"{sum(p['kind'] == 'table' for p in passages)} tables; "
          f"{len(passages)} passages from {len({p['report'] for p in passages})} reports, "
          f"median {lengths[len(lengths) // 2]} characters, "
          f"{sum(n < 200 for n in lengths)} shorter than 200 -> {PASSAGES}")


if __name__ == "__main__":
    main()
