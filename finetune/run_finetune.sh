#!/usr/bin/env bash
# Fine-tune the PaddleOCR recognition model on the human-transcribed TRAIN
# lines, validate on VAL, export an inference model. The TEST partition is
# never touched here.
#
#   conda activate penn-ocr
#   python -m penn_ocr.export_rec        # builds work/rec_dataset from the human log
#   bash finetune/run_finetune.sh        # extra args go to make_config.py, e.g. --epochs 40
#
# Result: work/finetune/inference, used by
#   python -m penn_ocr.predict --engine paddle --rec-model-dir work/finetune/inference --name paddle_finetuned
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MODEL="${MODEL:-PP-OCRv6_medium_rec}"
TAG="v3.7.0"
REPO="$ROOT/work/PaddleOCR"
OUT="${OUT:-$ROOT/work/finetune}"
WEIGHTS="$ROOT/work/pretrained/${MODEL}_pretrained.pdparams"

[ -d "$REPO" ] || git clone -q --depth 1 --branch "$TAG" https://github.com/PaddlePaddle/PaddleOCR.git "$REPO"
mkdir -p "$(dirname "$WEIGHTS")"
[ -f "$WEIGHTS" ] || curl -L --fail -o "$WEIGHTS" \
  "https://paddle-model-ecology.bj.bcebos.com/paddlex/official_pretrained_model/${MODEL}_pretrained.pdparams"

python "$ROOT/finetune/make_config.py" --model "$MODEL" --out "$OUT" "$@"
cd "$REPO"
echo "== Validation score of the pretrained model, before any training =="
python tools/eval.py -c "$OUT/config.yml" 2>&1 | tee "$OUT/eval_before.log" | grep -E "acc|norm_edit_dis|fps" || true
python "$ROOT/finetune/train_lines.py" -c "$OUT/config.yml" 2>&1 | tee "$OUT/train.log"
echo "== Validation score of the best fine-tuned checkpoint =="
python tools/eval.py -c "$OUT/config.yml" -o Global.checkpoints="$OUT/checkpoints/best_accuracy" \
  2>&1 | tee "$OUT/eval_after.log" | grep -E "acc|norm_edit_dis|fps" || true
python tools/export_model.py -c "$OUT/config.yml" \
  -o Global.pretrained_model="$OUT/checkpoints/best_accuracy" Global.save_inference_dir="$OUT/inference"
echo "Fine-tuned recognition model exported to $OUT/inference"
