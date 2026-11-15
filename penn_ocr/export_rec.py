"""Export human-transcribed TRAIN and VAL samples as a PaddleOCR text-line
recognition dataset (the held-out test partition is never exported).

    python -m penn_ocr.export_rec

A paragraph becomes line images only when the annotator typed the same number
of lines the detector found, so each typed line can be paired with its box.
Output: work/rec_dataset/{train,val}/*.png and rec_gt_{train,val}.txt
("relative/path<TAB>text", the format PaddleOCR's SimpleDataSet reads).
"""
import shutil

import cv2

from . import groundtruth, store
from .config import CROPS, REC_DATASET

LINE_PAD = 4


def main():
    boxes = store.sample_lines()
    if REC_DATASET.exists():
        shutil.rmtree(REC_DATASET)
    REC_DATASET.mkdir(parents=True)
    counts, skipped = {"train": 0, "val": 0}, []
    labels = {"train": [], "val": []}
    for r in groundtruth.build():
        if r["split"] not in labels or "illegible" in r["flags"]:
            continue
        typed, rows = r["text"].split("\n"), boxes[r["sample_id"]]
        if len(typed) != len(rows):
            skipped.append(r["sample_id"])
            continue
        crop = cv2.imread(str(CROPS / f"{r['sample_id']}.png"))
        h, w = crop.shape[:2]
        for i, (text, (x0, y0, x1, y1)) in enumerate(zip(typed, rows)):
            if not text.strip() or "[?]" in text:
                continue
            line = crop[max(0, y0 - LINE_PAD):min(h, y1 + LINE_PAD),
                        max(0, x0 - LINE_PAD):min(w, x1 + LINE_PAD)]
            rel = f"{r['split']}/{r['sample_id']}_l{i:02d}.png"
            (REC_DATASET / r["split"]).mkdir(parents=True, exist_ok=True)
            cv2.imwrite(str(REC_DATASET / rel), line)
            labels[r["split"]].append(f"{rel}\t{text.strip()}")
            counts[r["split"]] += 1
    for split, rows in labels.items():
        (REC_DATASET / f"rec_gt_{split}.txt").write_text("\n".join(rows) + ("\n" if rows else ""))
    print(f"line images: {counts} -> {REC_DATASET}")
    if skipped:
        print(f"skipped {len(skipped)} paragraphs with a typed/detected line-count mismatch:")
        for s in skipped:
            print("  ", s)


if __name__ == "__main__":
    main()
