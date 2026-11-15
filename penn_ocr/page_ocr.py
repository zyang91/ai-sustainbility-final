"""Step 1 (Vision 1.2 baseline): run pretrained PaddleOCR + layout detection on
a seeded random sample of pages from every scanned document.

Outputs per page:
  work/pages/<doc_id>/p0007.png      orientation-corrected page image (200 dpi)
  work/page_ocr/<doc_id>/p0007.json  text lines, confidences, layout blocks

    python -m penn_ocr.page_ocr --pages-per-doc 10
"""
import argparse
import json
import random
import time

import cv2
import numpy as np
import pymupdf

from . import documents, engines
from .config import DATA, DPI, PAGE_OCR, PAGES, SEED


def sample_pages(doc: dict, k: int) -> list[int]:
    """Seeded sample of 1-based page numbers, spread across the document."""
    pages = list(range(doc["first_content_page"], doc["n_pages"] + 1))
    rng = random.Random(f"{SEED}-{doc['doc_id']}")
    if len(pages) <= k:
        return pages
    # one page from each of k equal strata -> covers front matter, body, appendix
    bounds = np.linspace(0, len(pages), k + 1).astype(int)
    return [rng.choice(pages[a:b]) for a, b in zip(bounds[:-1], bounds[1:]) if b > a]


def render(pdf, page_no: int) -> np.ndarray:
    pm = pdf[page_no - 1].get_pixmap(dpi=DPI, colorspace=pymupdf.csRGB)
    rgb = np.frombuffer(pm.samples, np.uint8).reshape(pm.height, pm.width, 3)
    return cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pages-per-doc", type=int, default=10)
    ap.add_argument("--docs", nargs="*", help="limit to these doc_ids")
    args = ap.parse_args()

    docs = [d for d in documents.load() if d["source"] == "scan"
            and (not args.docs or d["doc_id"] in args.docs)]
    todo = []
    for d in docs:
        for p in sample_pages(d, args.pages_per_doc):
            out = PAGE_OCR / d["doc_id"] / f"p{p:04d}.json"
            if not out.exists():
                todo.append((d, p, out))
    print(f"{len(todo)} pages to OCR across {len(docs)} documents", flush=True)
    if not todo:
        return
    ocr, layout = engines.paddle_ocr(orientation=True), engines.paddle_layout()
    for i, (d, p, out) in enumerate(todo, 1):
        t0 = time.time()
        with pymupdf.open(DATA / d["path"]) as pdf:
            img = render(pdf, p)
        res = ocr.predict(img)[0]
        upright = res["doc_preprocessor_res"]["output_img"]
        blocks = [dict(label=b["label"], score=round(float(b["score"]), 3),
                       box=[int(v) for v in b["coordinate"]])
                  for b in layout.predict(upright)[0]["boxes"]]
        img_path = PAGES / d["doc_id"] / f"p{p:04d}.png"
        img_path.parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(img_path), upright)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(dict(
            doc_id=d["doc_id"], page=p, dpi=DPI,
            rotation=int(res["doc_preprocessor_res"]["angle"]),
            height=upright.shape[0], width=upright.shape[1],
            det_model=engines.PADDLE_DET_MODEL, rec_model=engines.PADDLE_REC_MODEL,
            layout_model=engines.PADDLE_LAYOUT_MODEL,
            seconds=round(time.time() - t0, 2),
            lines=engines.paddle_lines(res), blocks=blocks), indent=1))
        print(f"[{i}/{len(todo)}] {d['doc_id']} p{p}: {len(res['rec_texts'])} lines, "
              f"{time.time() - t0:.1f}s", flush=True)


if __name__ == "__main__":
    main()
