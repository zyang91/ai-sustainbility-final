"""Assemble the full text corpus from every document.

Scanned plans (1948-1998): text comes from the page OCR JSON written by
`python -m penn_ocr.page_ocr --all` (pretrained PP-OCRv6, the configuration
selected in docs/ocr_models.md). Born-digital plans (2006-2018): text is read
from the PDF's own text layer, no OCR.

    python -m penn_ocr.corpus

Page verdicts from the page review app (annotation/page_checks.jsonl) are
applied: "keep" restores text the layout model filed under a figure, "drop"
removes a page that holds only noise.

Outputs in work/corpus/:
  paragraphs.jsonl   one record per text block: doc_id, report, duplicate_of,
                     year, title, status,
                     source, page, block, prose, fluency, label, text, lines, confidence
                     (`prose` marks running sentences; analysis uses only those.
                     `fluency` is the language-model score from
                     `penn_ocr.fluency`, recorded but not used to filter)
  <doc_id>.txt       the same text as a readable file with page markers
  coverage.csv       pages expected / present, characters, mean confidence
"""
import csv
import json
import re

import pymupdf

from . import documents, engines, fluency, pagecheck
from .config import CORPUS, DATA, PAGE_OCR

# Layout labels whose text is not running prose and would pollute the corpus.
SKIP_LABELS = {"image", "chart", "seal", "formula", "header_image", "footer_image"}
# Labels that can hold running prose. Titles, headers, page numbers, tables,
# contents lists and captions are kept in paragraphs.jsonl but are not prose.
PROSE_LABELS = {"text", "abstract", "footnote", "reference", "algorithm", "unassigned", "image"}
PROSE_MIN_WORDS = 8
PROSE_MIN_WORDS_ITEM = 4     # a short list item that ends like a sentence
PROSE_MIN_CONFIDENCE = 0.8
WIDE = 0.6          # a block wider than this share of the page spans all columns


def join_lines(lines: list[str]) -> str:
    """One paragraph string; a word hyphenated across a line break is rejoined."""
    out = ""
    for ln in (l.strip() for l in lines if l.strip()):
        if out.endswith("-") and ln[:1].islower() and re.search(r"[a-z]-$", out):
            out = out[:-1] + ln
        else:
            out = f"{out} {ln}" if out else ln
    return out


def is_prose(para: dict) -> bool:
    """True for a block of running sentences, the input to semantic analysis.

    Leaves out what is left on a scanned plan besides its prose: map and
    legend labels (few words, or all capitals), tables of figures, running
    headers, handwriting and stray marks (low recognition confidence).
    """
    text = para["text"].strip()
    letters = sum(c.isalpha() for c in text)
    words = len(re.findall(r"[A-Za-z][A-Za-z'\-]+", text))
    # "(d) Quarters for junior faculty members." is a list item, not a label
    enough = words >= PROSE_MIN_WORDS or (words >= PROSE_MIN_WORDS_ITEM and text[-1:] in ".;:")
    if para["label"] not in PROSE_LABELS or not enough:
        return False
    if letters < 0.7 * len(text.replace(" ", "")) or sum(c.islower() for c in text) < 0.6 * letters:
        return False
    return para["confidence"] is None or para["confidence"] >= PROSE_MIN_CONFIDENCE


def order_blocks(blocks: list[dict], width: int) -> list[dict]:
    """Reading order: full-width blocks split the page into bands; inside a
    band the left column is read before the right one."""
    blocks = sorted(blocks, key=lambda b: b["box"][1])
    out, band = [], []

    def flush():
        left = [b for b in band if (b["box"][0] + b["box"][2]) / 2 < width / 2]
        right = [b for b in band if (b["box"][0] + b["box"][2]) / 2 >= width / 2]
        out.extend(left + right)
        band.clear()

    for b in blocks:
        if b["box"][2] - b["box"][0] > WIDE * width:
            flush()
            out.append(b)
        else:
            band.append(b)
    flush()
    return out


def assign(page: dict) -> list[dict]:
    """Layout blocks of one OCR'd page, each with the text lines that fall in it."""
    blocks = [dict(b, lines=[]) for b in page["blocks"]]
    loose = []
    for ln in page["lines"]:
        cx, cy = (ln["box"][0] + ln["box"][2]) / 2, (ln["box"][1] + ln["box"][3]) / 2
        inside = [b for b in blocks if b["box"][0] <= cx <= b["box"][2] and b["box"][1] <= cy <= b["box"][3]]
        if inside:          # the smallest containing block is the most specific
            min(inside, key=lambda b: (b["box"][2] - b["box"][0]) * (b["box"][3] - b["box"][1]))["lines"].append(ln)
        else:
            loose.append(ln)
    # lines outside every layout block: keep them, one pseudo-block per row
    for row in engines.reading_order(loose):
        box = [min(l["box"][0] for l in row), min(l["box"][1] for l in row),
               max(l["box"][2] for l in row), max(l["box"][3] for l in row)]
        blocks.append(dict(label="unassigned", box=box, lines=row))
    return [b for b in blocks if b["lines"]]


def scan_page(page: dict, keep_all: bool = False) -> list[dict]:
    """Paragraph records for one OCR'd page.

    `keep_all`: also keep text inside figure-type blocks. Set for pages a
    person marked as body text after the layout model called them an image.
    """
    out = []
    for b in order_blocks([b for b in assign(page) if keep_all or b["label"] not in SKIP_LABELS],
                          page["width"]):
        rows = [" ".join(l["text"] for l in r) for r in engines.reading_order(b["lines"])]
        text = join_lines(rows)
        if text:
            out.append(dict(label=b["label"], text=text, lines=rows,
                            confidence=round(sum(l["score"] for l in b["lines"]) / len(b["lines"]), 4)))
    return out


def pdf_page(page) -> list[dict]:
    """Paragraph records from a born-digital page's own text layer.

    The PDF's native block order follows the designer's reading order (sorting
    by position would interleave columns). Many of these PDFs store each
    printed line as its own block, so consecutive blocks in the same column
    with normal line spacing are merged back into one paragraph.
    """
    paras, prev = [], None
    for x0, y0, x1, y1, text, _, kind in page.get_text("blocks"):
        rows = [l.strip() for l in text.split("\n") if l.strip()]
        if kind != 0 or not rows:
            continue
        line_h = (y1 - y0) / len(rows)
        if prev and abs(x0 - prev["x0"]) < 8 and 0 <= y0 - prev["y1"] < 1.2 * min(line_h, prev["line_h"]):
            prev["rows"] += rows
        else:
            prev = dict(rows=rows, x0=x0)
            paras.append(prev)
        prev.update(y1=y1, line_h=line_h)
    return [dict(label="text", text=join_lines(p["rows"]), lines=p["rows"], confidence=None)
            for p in paras]


def main():
    CORPUS.mkdir(parents=True, exist_ok=True)
    coverage, verdicts, scores = [], pagecheck.verdicts(), fluency.load()
    with open(CORPUS / "paragraphs.jsonl", "w") as jl:
        for d in documents.load():
            pages = range(d["first_content_page"], d["n_pages"] + 1)
            got, chars, prose_chars, confs, txt = 0, 0, 0, [], []
            pdf = pymupdf.open(DATA / d["path"]) if d["source"] != "scan" else None
            for p in pages:
                if pdf is not None:
                    paras = pdf_page(pdf[p - 1])
                else:
                    f = PAGE_OCR / d["doc_id"] / f"p{p:04d}.json"
                    if not f.exists():
                        continue
                    verdict = verdicts.get((d["doc_id"], p))
                    paras = [] if verdict == "drop" else \
                        scan_page(json.loads(f.read_text()), keep_all=verdict == "keep")
                got += 1
                txt.append(f"\n===== page {p} =====\n")
                for i, para in enumerate(paras):
                    jl.write(json.dumps(dict(
                        doc_id=d["doc_id"], report=d["report"], duplicate_of=d["duplicate_of"],
                        year=d["year"], title=d["title"], status=d["status"],
                        source="pdf_text" if pdf is not None else "ocr", page=p, block=i,
                        prose=is_prose(para), fluency=scores.get(fluency.key(para["text"])),
                        **para),
                        ensure_ascii=False) + "\n")
                    txt.append(para["text"] + "\n")
                    chars += len(para["text"])
                    prose_chars += len(para["text"]) if is_prose(para) else 0
                    if para["confidence"] is not None:
                        confs.append(para["confidence"])
            if pdf is not None:
                pdf.close()
            (CORPUS / f"{d['doc_id']}.txt").write_text("\n".join(txt))
            coverage.append(dict(doc_id=d["doc_id"], report=d["report"],
                                 duplicate_of=d["duplicate_of"], year=d["year"], source=d["source"],
                                 pages_expected=len(pages), pages_done=got, characters=chars,
                                 prose_characters=prose_chars,
                                 mean_confidence=round(sum(confs) / len(confs), 4) if confs else ""))
    with open(CORPUS / "coverage.csv", "w", newline="") as f:
        w = csv.DictWriter(f, list(coverage[0]))
        w.writeheader()
        w.writerows(coverage)
    done, total = sum(c["pages_done"] for c in coverage), sum(c["pages_expected"] for c in coverage)
    print(f"{done} of {total} pages, {sum(c['characters'] for c in coverage):,} characters "
          f"({sum(c['prose_characters'] for c in coverage):,} in prose blocks) -> {CORPUS}")
    for c in coverage:
        if c["pages_done"] < c["pages_expected"]:
            print(f"  incomplete: {c['doc_id']} {c['pages_done']}/{c['pages_expected']}")


if __name__ == "__main__":
    main()
