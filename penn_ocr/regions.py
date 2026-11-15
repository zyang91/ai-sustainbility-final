"""Step 2 (Vision 1.3): choose the paragraph regions a human will transcribe.

Reads the page-level baseline output, keeps layout blocks labelled as body
text, and draws a small sample that is balanced across documents (and so
across periods, typefaces and layouts) and across scan-quality levels.
Writes the crops plus a manifest that contains NO model text:

  work/crops/<sample_id>.png
  annotation/samples.csv        metadata, page box, split, queue order
  annotation/sample_lines.json  detected line boxes inside each crop

    python -m penn_ocr.regions --per-doc 6
"""
import argparse
import csv
import json
import random
from collections import Counter, defaultdict

import cv2

from . import documents, engines, store
from .config import CROPS, PAGE_OCR, PAGES, SAMPLE_LINES, SAMPLES_CSV, SEED

MIN_LINES, MAX_LINES = 3, 12      # keep typing effort per sample reasonable
MIN_CHARS = 60
MAX_PER_PAGE = 2
PAD = 8                           # px of context around the paragraph

# Train / validation / test are separated at PAGE level inside each document:
# every paragraph from one page lands in one partition.
PAGE_SPLIT_CYCLE = ["train", "test", "train", "val", "test", "train", "train", "val"]

# The 1961, 1963 and 1966 Development Plans are successive editions of the same
# text and the archive holds two scans of each. Page-level splitting would put
# the same sentences in train and test, so this family is split by DOCUMENT:
# both scans of an edition always share a partition.
DOCUMENT_SPLIT = {
    "1961_dev_plan_taubin": "train", "1961_dev_plan": "train",
    "1963_dev_plan_taubin": "val", "1963_dev_plan": "val",
    "1966_campus_dev_plan_ua": "test", "1966_campus_dev_plan": "test",
}

FIELDS = ["order", "sample_id", "doc_id", "year", "title", "status", "page",
          "x0", "y0", "x1", "y1", "rotation", "n_lines", "split", "quality_bin"]


def candidates(page: dict) -> list[dict]:
    """Body-text blocks on one page with their detected lines."""
    out = []
    blocks = [b for b in page["blocks"] if b["label"] == "text" and b["score"] >= 0.5]
    for bi, b in enumerate(sorted(blocks, key=lambda b: (b["box"][1], b["box"][0]))):
        x0, y0, x1, y1 = b["box"]
        inside = [l for l in page["lines"]
                  if x0 - 5 <= (l["box"][0] + l["box"][2]) / 2 <= x1 + 5
                  and y0 - 5 <= (l["box"][1] + l["box"][3]) / 2 <= y1 + 5]
        rows = engines.reading_order(inside)
        text = " ".join(l["text"] for r in rows for l in r)
        if not (MIN_LINES <= len(rows) <= MAX_LINES) or len(text) < MIN_CHARS:
            continue
        letters = sum(c.isalpha() for c in text) / max(1, len(text))
        if letters < 0.6:           # numeric tables / schedules mislabelled as text
            continue
        row_boxes = [[min(l["box"][0] for l in r), min(l["box"][1] for l in r),
                      max(l["box"][2] for l in r), max(l["box"][3] for l in r)] for r in rows]
        cx0 = max(0, min([x0] + [r[0] for r in row_boxes]) - PAD)
        cy0 = max(0, min([y0] + [r[1] for r in row_boxes]) - PAD)
        cx1 = min(page["width"], max([x1] + [r[2] for r in row_boxes]) + PAD)
        cy1 = min(page["height"], max([y1] + [r[3] for r in row_boxes]) + PAD)
        # The layout model sometimes splits a paragraph mid-way, so the line just
        # above or below is not part of this sample but pokes into the crop.
        # Pull the edge in so the annotator never sees half a line.
        top, bottom = row_boxes[0][1], row_boxes[-1][3]
        for l in page["lines"]:
            lx0, ly0, lx1, ly1 = l["box"][:4]
            if any(l is m for m in inside) or min(lx1, cx1) - max(lx0, cx0) <= 0:
                continue
            if (ly0 + ly1) / 2 < top and ly1 > cy0:
                cy0 = max(cy0, min(ly1, top) - 2)
            if (ly0 + ly1) / 2 > bottom and ly0 < cy1:
                cy1 = min(cy1, max(ly0, bottom) + 2)
        out.append(dict(
            doc_id=page["doc_id"], page=page["page"], rotation=page["rotation"], block=bi,
            box=[cx0, cy0, cx1, cy1],
            rows=[[r[0] - cx0, r[1] - cy0, r[2] - cx0, r[3] - cy0] for r in row_boxes],
            conf=sum(l["score"] for l in inside) / len(inside)))
    return out


# The 1961/1963/1966 plans reprint passages from one another and each was scanned
# twice, so the same paragraph can be drawn from two files. Listed here: the copy
# that is dropped, and the sample that already covers that text.
EXCLUDE = {
    "1961_dev_plan_p0002_b01": "1961_dev_plan_taubin_p0004_b00",
    "1961_dev_plan_taubin_p0135_b07": "1966_campus_dev_plan_p0008_b06",   # was train vs test
}


def select(per_doc: int) -> list[dict]:
    docs = {d["doc_id"]: d for d in documents.load() if d["source"] == "scan"}
    pool = defaultdict(lambda: defaultdict(list))        # doc -> page -> regions
    for f in sorted(PAGE_OCR.glob("*/p*.json")):
        page = json.loads(f.read_text())
        if page["doc_id"] in docs:
            for c in candidates(page):
                pool[c["doc_id"]][c["page"]].append(c)

    # scan-quality proxy: terciles of baseline confidence over the whole pool
    confs = sorted(c["conf"] for pages in pool.values() for cs in pages.values() for c in cs)
    lo, hi = confs[len(confs) // 3], confs[2 * len(confs) // 3]
    for pages in pool.values():
        for cs in pages.values():
            for c in cs:
                c["quality_bin"] = "low" if c["conf"] < lo else "high" if c["conf"] >= hi else "mid"

    chosen = defaultdict(list)
    for doc_id in docs:
        rng = random.Random(f"{SEED}-regions-{doc_id}")
        pages = sorted(pool.get(doc_id, {}))
        rng.shuffle(pages)
        split_of = {p: DOCUMENT_SPLIT.get(doc_id, PAGE_SPLIT_CYCLE[i % len(PAGE_SPLIT_CYCLE)])
                    for i, p in enumerate(pages)}
        taken, seen_bins = Counter(), Counter()
        while len(chosen[doc_id]) < per_doc:
            progressed = False
            for p in pages:          # round-robin: spread over pages before doubling up
                left = [c for c in pool[doc_id][p] if "picked" not in c]
                if not left or taken[p] >= MAX_PER_PAGE or len(chosen[doc_id]) >= per_doc:
                    continue
                rng.shuffle(left)
                c = min(left, key=lambda c: seen_bins[c["quality_bin"]])  # balance quality
                c["picked"], c["split"] = True, split_of[p]
                taken[p] += 1
                seen_bins[c["quality_bin"]] += 1
                chosen[doc_id].append(c)
                progressed = True
            if not progressed:
                break

    # queue order interleaves documents, so any prefix the annotator finishes
    # is still spread across the archive
    rows, order = [], 0
    ordered_docs = sorted(docs, key=lambda d: (docs[d]["year"], d))
    for rnd in range(per_doc):
        for doc_id in ordered_docs:
            if rnd < len(chosen[doc_id]):
                c, d = chosen[doc_id][rnd], docs[doc_id]
                order += 1
                rows.append(dict(
                    order=order, sample_id=f"{doc_id}_p{c['page']:04d}_b{c['block']:02d}",
                    doc_id=doc_id, year=d["year"], title=d["title"], status=d["status"],
                    page=c["page"], x0=c["box"][0], y0=c["box"][1], x1=c["box"][2], y1=c["box"][3],
                    rotation=c["rotation"], n_lines=len(c["rows"]), split=c["split"],
                    quality_bin=c["quality_bin"], _rows=c["rows"]))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-doc", type=int, default=6)
    ap.add_argument("--force", action="store_true",
                    help="allow dropping samples that already have transcriptions")
    args = ap.parse_args()

    rows = [r for r in select(args.per_doc) if r["sample_id"] not in EXCLUDE]
    for i, r in enumerate(rows, 1):
        r["order"] = i
    done = set(store.latest()) - {r["sample_id"] for r in rows}
    if done and not args.force:
        raise SystemExit(f"{len(done)} transcribed samples would be dropped; use --force to accept.")

    CROPS.mkdir(parents=True, exist_ok=True)
    lines = {}
    for r in rows:
        page = cv2.imread(str(PAGES / r["doc_id"] / f"p{r['page']:04d}.png"))
        cv2.imwrite(str(CROPS / f"{r['sample_id']}.png"), page[r["y0"]:r["y1"], r["x0"]:r["x1"]])
        lines[r["sample_id"]] = r.pop("_rows")
    with open(SAMPLES_CSV, "w", newline="") as f:
        w = csv.DictWriter(f, FIELDS)
        w.writeheader()
        w.writerows(rows)
    SAMPLE_LINES.write_text(json.dumps(lines))

    print(f"{len(rows)} samples from {len({r['doc_id'] for r in rows})} documents, "
          f"{len({(r['doc_id'], r['page']) for r in rows})} pages, "
          f"{sum(r['n_lines'] for r in rows)} text lines")
    print("split:  ", dict(Counter(r["split"] for r in rows)))
    print("quality:", dict(Counter(r["quality_bin"] for r in rows)))
    leak = defaultdict(set)
    for r in rows:
        leak[(r["doc_id"], r["page"])].add(r["split"])
    assert all(len(s) == 1 for s in leak.values()), "a page is in two partitions"


if __name__ == "__main__":
    main()
