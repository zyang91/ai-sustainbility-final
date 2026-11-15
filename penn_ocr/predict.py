"""Run an OCR engine on the sampled paragraph crops (the benchmark inputs).

    python -m penn_ocr.predict --engine paddle
    python -m penn_ocr.predict --engine paddle --rec-model-dir work/finetune/inference --name paddle_finetuned
    python -m penn_ocr.predict --engine doctr

Every engine sees exactly the same crop images. Output:
work/predictions/<name>.jsonl with one {"sample_id", "text", "lines", "seconds"} per crop.
"""
import argparse
import json
import time

import cv2

from . import engines, store
from .config import CROPS, PREDICTIONS


def paddle_runner(rec_model_dir=None):
    ocr = engines.paddle_ocr(orientation=False, rec_model_dir=rec_model_dir)

    def run(img):
        rows = engines.reading_order(engines.paddle_lines(ocr.predict(img)[0]))
        return [" ".join(l["text"] for l in r) for r in rows]
    return run


def doctr_runner():
    from doctr.models import ocr_predictor
    model = ocr_predictor(det_arch="db_resnet50", reco_arch="crnn_vgg16_bn", pretrained=True)

    def run(img):
        page = model([cv2.cvtColor(img, cv2.COLOR_BGR2RGB)]).pages[0]
        return [" ".join(w.value for w in line.words)
                for block in page.blocks for line in block.lines]
    return run


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--engine", choices=["paddle", "doctr"], required=True)
    ap.add_argument("--rec-model-dir", help="fine-tuned PaddleOCR recognition model")
    ap.add_argument("--name", help="prediction file name (default: engine name)")
    args = ap.parse_args()
    name = args.name or ("paddle_pretrained" if args.engine == "paddle" else "doctr_pretrained")
    run = paddle_runner(args.rec_model_dir) if args.engine == "paddle" else doctr_runner()

    PREDICTIONS.mkdir(parents=True, exist_ok=True)
    out = PREDICTIONS / f"{name}.jsonl"
    samples = store.samples()
    with open(out, "w") as f:
        for i, s in enumerate(samples, 1):
            img = cv2.imread(str(CROPS / f"{s['sample_id']}.png"))
            t0 = time.time()
            lines = run(img)
            f.write(json.dumps(dict(sample_id=s["sample_id"], text=" ".join(lines), lines=lines,
                                    seconds=round(time.time() - t0, 3)), ensure_ascii=False) + "\n")
            if i % 20 == 0 or i == len(samples):
                print(f"{i}/{len(samples)}", flush=True)
    print(f"-> {out}")


if __name__ == "__main__":
    main()
