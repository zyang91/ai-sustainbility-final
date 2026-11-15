"""Assemble the full text corpus from every document.

Scanned plans (1948-1998): text comes from the page OCR JSON written by
`python -m penn_ocr.page_ocr --all` (pretrained PP-OCRv6, the configuration
selected in docs/ocr_models.md). Born-digital plans (2006-2018): text is read
from the PDF's own text layer, no OCR.

    python -m penn_ocr.corpus

Outputs in work/corpus/:
  paragraphs.jsonl   one record per text block: doc_id, year, title, status,
                     source, page, block, label, text, lines, confidence
  <doc_id>.txt       the same text as a readable file with page markers
  coverage.csv       pages expected / present, characters, mean confidence
"""
import csv
import json
import re

import pymupdf

from . import documents, engines
from .config import CORPUS, DATA, PAGE_OCR

# Layout labels whose text is not running prose and would pollute the corpus.
SKIP_LABELS = {"image", "chart", "seal", "formula", "header_image", "footer_image"}
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


def scan_page(page: dict) -> list[dict]:
    """Paragraph records for one OCR'd page."""
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
    out = []
    for b in order_blocks([b for b in blocks if b["lines"] and b["label"] not in SKIP_LABELS],
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
    coverage = []
    with open(CORPUS / "paragraphs.jsonl", "w") as jl:
        for d in documents.load():
            pages = range(d["first_content_page"], d["n_pages"] + 1)
            got, chars, confs, txt = 0, 0, [], []
            pdf = pymupdf.open(DATA / d["path"]) if d["source"] != "scan" else None
            for p in pages:
                if pdf is not None:
                    paras = pdf_page(pdf[p - 1])
                else:
                    f = PAGE_OCR / d["doc_id"] / f"p{p:04d}.json"
                    if not f.exists():
                        continue
                    paras = scan_page(json.loads(f.read_text()))
                got += 1
                txt.append(f"\n===== page {p} =====\n")
                for i, para in enumerate(paras):
                    jl.write(json.dumps(dict(
                        doc_id=d["doc_id"], year=d["year"], title=d["title"], status=d["status"],
                        source="pdf_text" if pdf is not None else "ocr", page=p, block=i, **para),
                        ensure_ascii=False) + "\n")
                    txt.append(para["text"] + "\n")
                    chars += len(para["text"])
                    if para["confidence"] is not None:
                        confs.append(para["confidence"])
            if pdf is not None:
                pdf.close()
            (CORPUS / f"{d['doc_id']}.txt").write_text("\n".join(txt))
            coverage.append(dict(doc_id=d["doc_id"], year=d["year"], source=d["source"],
                                 pages_expected=len(pages), pages_done=got, characters=chars,
                                 mean_confidence=round(sum(confs) / len(confs), 4) if confs else ""))
    with open(CORPUS / "coverage.csv", "w", newline="") as f:
        w = csv.DictWriter(f, list(coverage[0]))
        w.writeheader()
        w.writerows(coverage)
    done, total = sum(c["pages_done"] for c in coverage), sum(c["pages_expected"] for c in coverage)
    print(f"{done} of {total} pages, {sum(c['characters'] for c in coverage):,} characters -> {CORPUS}")
    for c in coverage:
        if c["pages_done"] < c["pages_expected"]:
            print(f"  incomplete: {c['doc_id']} {c['pages_done']}/{c['pages_expected']}")


if __name__ == "__main__":
    main()
