# OCR models and settings (Vision 1.2)

Recorded before any benchmark number is produced. All values are set in
[penn_ocr/engines.py](../penn_ocr/engines.py) and
[finetune/make_config.py](../finetune/make_config.py).

## Primary engine: PaddleOCR

| Item | Value |
|---|---|
| Library | `paddleocr==3.7.0`, `paddlepaddle==3.3.1` (CPU, macOS arm64, Python 3.12) |
| License | Apache-2.0 (code and released weights) |
| Text detection | `PP-OCRv6_medium_det` |
| Text recognition | `PP-OCRv6_medium_rec` (the library default for English in 3.7.0) |
| Page orientation | `PP-LCNet_x1_0_doc_ori`, on for full pages, off for crops |
| Layout detection | `PP-DocLayout-L`, used only to find paragraph blocks for sampling |
| Unwarping, text-line orientation | off |
| Render resolution | 200 dpi from the source PDF |
| Thresholds | library defaults, no recognition score cut-off |

Page orientation matters here: several scans are upside-down or sideways
(for example the 1961 Development Plan). The classifier's rotation is stored
with every page so a crop can always be traced back to the PDF page.

## Comparison baseline: docTR (optional)

`python-doctr[torch]`, Apache-2.0, `db_resnet50` detection + `crnn_vgg16_bn`
recognition, pretrained weights. Not installed by default:

    pip install "python-doctr[torch]"
    python -m penn_ocr.predict --engine doctr

## Benchmark input

Every engine reads the same paragraph crop images (`work/crops/`), one
prediction per crop, lines joined with a space in reading order. Scores are
CER and WER against the human transcription after the light normalisation in
[penn_ocr/metrics.py](../penn_ocr/metrics.py). Only the test partition is
reported; validation is for choosing a fine-tuned checkpoint.

## Fine-tuning experiment

Only the **recognition** model is fine-tuned; detection stays pretrained.

| Item | Value |
|---|---|
| Training code | PaddleOCR repository, tag `v3.7.0` (`tools/train.py`) |
| Base config | `configs/rec/PP-OCRv6/PP-OCRv6_medium_rec.yml` |
| Starting weights | `PP-OCRv6_medium_rec_pretrained.pdparams` (official) |
| Training data | text-line images cut from human-transcribed **train** paragraphs |
| Model selection | best line accuracy on the **val** partition, checked every epoch |
| Test partition | never exported, never seen by training |

Changes from the stock config:

| Setting | Stock | Here | Why |
|---|---|---|---|
| `max_text_length` | 25 | 150 | Samples are full printed lines (60-90 characters). Longer labels are silently dropped at 25. |
| Train / eval image width | 320 px | 1280 px | A full line squeezed to 320 px is unreadable. |
| `RecConAug` | on | removed | It concatenates several samples; lines are already full width. |
| Learning rate | 5e-4, 5 warm-up epochs | 2e-5, 1 warm-up epoch | Small data, start from converged weights. |
| Training image height | 32, 48 or 64 px (multi-scale) | 48 px | Needed by the pooling change below. |
| Backbone pooling in training | fixed 40 columns | same as inference (1 column per 8 px) | See "Training-mode pooling". |
| BatchNorm in training | batch statistics | pretrained running statistics | Batches of 8 padded lines give noisy statistics. |
| Epochs / batch | 100 / 64 | 20 / 8 (Colab notebook) | A few hundred lines. |
| Device | GPU, distributed | one GPU (`--gpu`) or CPU | Paddle has no Apple-GPU backend; training runs on Colab. |

The first validation pass runs after the first epoch and the best checkpoint
is the one exported, so a run that never beats its early state exports
something close to the pretrained model. As the vision document says, the
fine-tuned model is kept only if it beats the pretrained baseline on held-out
data.

### Training-mode pooling (found 2026-11-15)

With pretrained weights and no update, training batches scored about 20 %
character similarity while the same model scored over 99 % in evaluation.
Cause: in training mode the PP-OCRv6 backbone (`rec_lcnetv4.py`) pools its
feature map to a fixed 40 columns, which fits 320 px word crops but cannot
spell a 70-character line. `finetune/train_lines.py` runs the stock
`tools/train.py` with the inference pooling used in training too, and with
BatchNorm statistics frozen. Measured on one clean validation batch in
training mode: 24 % character similarity stock, 87 % with the pooling change,
100 % with BatchNorm frozen as well. The PaddleOCR checkout itself is not
edited.

### Result (2026-11-15)

Run on a Colab GPU with `finetune/colab_finetune.ipynb`: 209 training lines,
20 epochs, learning rate 2e-5, batch 8, best checkpoint chosen on the 101
validation lines.

Validation line images, recognition only:

| Model | Exact lines | Character similarity |
|---|---|---|
| Pretrained | 95.0 % (96 of 101) | 99.64 % |
| Fine-tuned | 98.0 % (99 of 101) | 99.89 % |

Full pipeline (detection + recognition) on the benchmark paragraphs,
`python -m penn_ocr.evaluate`:

| Partition | Paragraphs | Characters | Pretrained CER / WER | Fine-tuned CER / WER | Character errors |
|---|---|---|---|---|---|
| test | 33 | 12,203 | 0.63 % / 1.21 % | 0.62 % / 1.11 % | 77 vs 76 |
| val | 20 | 5,711 | 1.24 % / 2.14 % | 1.21 % / 1.81 % | 71 vs 69 |
| train | 39 | 11,587 | 0.24 % / 0.91 % | 0.16 % / 0.59 % | 28 vs 18 |

Reading: on the held-out test partition the two models are tied. One
character error out of 12,203 is far below the 0.7 % disagreement between
two human typings, so it is not a measurable gain. On test the fine-tuned
model changed 9 paragraphs: 5 better, 3 worse, 1 equal. The gain on the
training partition is the model fitting lines it was trained on.

The remaining test errors are dominated by text lines the detector misses
(`1966_campus_dev_plan_ua`, about 5 % CER under both models), which
recognition fine-tuning cannot change.

Conclusion: fine-tuning the recognition model on 209 lines does not beat the
pretrained baseline on held-out documents. Following the vision document,
the pretrained PP-OCRv6 model stays the choice for full-corpus digitization.

Caveat: the ground truth was checked against the pretrained model's output
(see README, "Check mismatched lines"), which favours the pretrained model
slightly.

### Notes

- CPU training on this Mac takes about 56 s per batch of 8; the Colab T4 run
  took about 0.7 s per batch.
