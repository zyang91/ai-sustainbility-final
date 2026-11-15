"""Score prediction files against the human ground truth.

    python -m penn_ocr.evaluate                 # every engine, test partition
    python -m penn_ocr.evaluate --split val --by-doc

Only the held-out TEST partition is reported by default; use `--split val`
for model selection while fine-tuning.
"""
import argparse
import json
from collections import defaultdict

from . import groundtruth, metrics
from .config import PREDICTIONS


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", default="test", choices=["train", "val", "test", "all"])
    ap.add_argument("--by-doc", action="store_true")
    args = ap.parse_args()

    truth = {r["sample_id"]: r for r in groundtruth.build()
             if args.split in ("all", r["split"])}
    if not truth:
        raise SystemExit(f"No ground truth yet for split '{args.split}'. Transcribe some samples first.")
    files = sorted(PREDICTIONS.glob("*.jsonl"))
    if not files:
        raise SystemExit("No predictions. Run: python -m penn_ocr.predict --engine paddle")
    print(f"split={args.split}: {len(truth)} human-transcribed samples\n")
    print(f"{'engine':28s} {'n':>4s} {'CER':>8s} {'WER':>8s} {'sec/crop':>9s}")
    for f in files:
        preds = {r["sample_id"]: r for r in map(json.loads, open(f))}
        ids = [i for i in truth if i in preds]
        m = metrics.corpus([(truth[i]["text"], preds[i]["text"]) for i in ids])
        secs = sum(preds[i]["seconds"] for i in ids) / max(1, len(ids))
        print(f"{f.stem:28s} {m['n']:4d} {m['cer']:8.4f} {m['wer']:8.4f} {secs:9.2f}")
        if args.by_doc:
            by = defaultdict(list)
            for i in ids:
                by[truth[i]["doc_id"]].append((truth[i]["text"], preds[i]["text"]))
            for doc, pairs in sorted(by.items()):
                d = metrics.corpus(pairs)
                print(f"   {doc:25s} {d['n']:4d} {d['cer']:8.4f} {d['wer']:8.4f}")


if __name__ == "__main__":
    main()
