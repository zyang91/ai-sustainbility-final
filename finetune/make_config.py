"""Write the fine-tuning config for the PaddleOCR recognition model.

Starts from the official PP-OCRv6_medium_rec training config in the pinned
PaddleOCR checkout and changes only what a small CPU fine-tune on
historical text lines needs. Every change is listed in docs/ocr_models.md.
"""
import argparse
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from penn_ocr.config import REC_DATASET, WORK  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--model", default="PP-OCRv6_medium_rec")
ap.add_argument("--epochs", type=int, default=10)
ap.add_argument("--lr", type=float, default=2e-5)
ap.add_argument("--batch-size", type=int, default=8)
ap.add_argument("--data", default=str(REC_DATASET))
ap.add_argument("--out", default=str(WORK / "finetune"))
args = ap.parse_args()

repo, out, data = WORK / "PaddleOCR", Path(args.out), Path(args.data)
cfg = yaml.safe_load((repo / f"configs/rec/PP-OCRv6/{args.model}.yml").read_text())
n_train = sum(1 for _ in open(data / "rec_gt_train.txt"))
steps_per_epoch = max(1, n_train // args.batch_size)

g = cfg["Global"]
g.update(use_gpu=False, distributed=False, epoch_num=args.epochs,
         pretrained_model=str(WORK / "pretrained" / f"{args.model}_pretrained"),
         save_model_dir=str(out / "checkpoints"), save_inference_dir=str(out / "inference"),
         character_dict_path=str(repo / g["character_dict_path"]),
         save_epoch_step=args.epochs, print_batch_step=5,
         eval_batch_step=[0, steps_per_epoch],          # validate once per epoch
         max_text_length=150)                           # full printed lines, not single words
cfg["Architecture"]["Head"]["head_list"][1]["NRTRHead"]["max_text_length"] = 150
cfg["Optimizer"]["lr"].update(learning_rate=args.lr, warmup_epoch=1)

tr = cfg["Train"]
tr["dataset"].update(data_dir=str(data), label_file_list=[str(data / "rec_gt_train.txt")],
                     ratio_list=[1.0])
# RecConAug glues several training lines into one image; our lines are already
# full-width, so it is removed. RecAug (blur, noise, jitter) is kept.
tr["dataset"]["transforms"] = [t for t in tr["dataset"]["transforms"] if "RecConAug" not in t]
for t in tr["dataset"]["transforms"]:
    if "MultiLabelEncode" in t:
        t["MultiLabelEncode"]["max_text_length"] = 150
tr["dataset"]["ext_op_transform_idx"] = 1
# The stock sampler squeezes every image to 320 px wide, which is right for
# single words but makes a 70-character line unreadable. Train at the same
# 1280 px width used for validation.
tr["sampler"].update(first_bs=args.batch_size, scales=[[1280, 32], [1280, 48], [1280, 64]])
tr["loader"].update(batch_size_per_card=args.batch_size, num_workers=0,
                    drop_last=n_train >= args.batch_size)

ev = cfg["Eval"]
ev["dataset"].update(data_dir=str(data), label_file_list=[str(data / "rec_gt_val.txt")])
for t in ev["dataset"]["transforms"]:
    if "MultiLabelEncode" in t:
        t["MultiLabelEncode"]["max_text_length"] = 150
    if "RecResizeImg" in t:
        t["RecResizeImg"]["image_shape"] = [3, 48, 1280]   # keep long lines legible
ev["loader"].update(batch_size_per_card=8, num_workers=0)

out.mkdir(parents=True, exist_ok=True)
(out / "config.yml").write_text(yaml.safe_dump(cfg, sort_keys=False))
print(f"{n_train} training lines, {steps_per_epoch} steps/epoch -> {out / 'config.yml'}")
