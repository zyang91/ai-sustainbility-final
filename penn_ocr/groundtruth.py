"""Build the benchmark table from the human transcription log.

    python -m penn_ocr.groundtruth

Writes annotation/ground_truth.csv (one row per usable transcribed sample) and
prints coverage by partition and document, plus first/second-pass agreement.
"""
import csv
from collections import Counter

from . import metrics, store
from .config import GROUND_TRUTH_CSV

FIELDS = ["sample_id", "doc_id", "year", "status", "page", "split", "text",
          "n_lines_typed", "n_lines_detected", "flags", "notes", "annotator",
          "reference_pass", "second_pass_cer", "saved_at"]


def build() -> list[dict]:
    log, rows = store.latest(), []
    for s in store.samples():
        passes = log.get(s["sample_id"], {})
        ref = store.reference(passes)
        if not ref or "unusable" in ref["flags"] or not ref["text"]:
            continue
        agree = ""
        if "first" in passes and "second" in passes:
            agree = round(metrics.cer(passes["first"]["text"], passes["second"]["text"]), 4)
        rows.append(dict(
            sample_id=s["sample_id"], doc_id=s["doc_id"], year=s["year"], status=s["status"],
            page=s["page"], split=s["split"], text=ref["text"],
            n_lines_typed=ref["text"].count("\n") + 1, n_lines_detected=s["n_lines"],
            flags=";".join(ref["flags"]), notes=ref["notes"], annotator=ref["annotator"],
            reference_pass=ref["pass"], second_pass_cer=agree, saved_at=ref["saved_at"]))
    with open(GROUND_TRUTH_CSV, "w", newline="") as f:
        w = csv.DictWriter(f, FIELDS)
        w.writeheader()
        w.writerows(rows)
    return rows


def main():
    rows, total = build(), store.samples()
    print(f"{len(rows)} usable transcriptions of {len(total)} sampled regions -> {GROUND_TRUTH_CSV}")
    if not rows:
        return
    planned = Counter(s["split"] for s in total)
    got = Counter(r["split"] for r in rows)
    for sp in ("train", "val", "test"):
        print(f"  {sp:5s} {got[sp]:3d} / {planned[sp]}")
    print(f"  documents covered: {len({r['doc_id'] for r in rows})} / {len({s['doc_id'] for s in total})}")
    print(f"  words: {sum(len(r['text'].split()) for r in rows)}, "
          f"lines: {sum(r['n_lines_typed'] for r in rows)}")
    mism = [r["sample_id"] for r in rows if r["n_lines_typed"] != r["n_lines_detected"]]
    if mism:
        print(f"  {len(mism)} samples whose typed line count differs from the detector "
              f"(usable for the benchmark, skipped for line-level fine-tuning)")
    double = [r["second_pass_cer"] for r in rows if r["second_pass_cer"] != ""]
    if double:
        print(f"  double-keyed: {len(double)}, mean first-vs-second CER {sum(double) / len(double):.4f}")
    flagged = Counter(f for r in rows for f in r["flags"].split(";") if f)
    if flagged:
        print("  flags:", dict(flagged))


if __name__ == "__main__":
    main()
