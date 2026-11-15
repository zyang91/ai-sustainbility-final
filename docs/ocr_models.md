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
| Epochs / batch | 100 / 64 | 10 / 8 | CPU training on a few hundred lines. |
| Device | GPU, distributed | CPU, single process | No CUDA on this machine; Paddle has no Apple-GPU backend. |

The first validation pass runs after the first epoch and the best checkpoint
is the one exported, so a run that never beats its early state exports
something close to the pretrained model. As the vision document says, the
fine-tuned model is kept only if it beats the pretrained baseline on held-out
data.

### Known limits (checked 2026-11-14 with a throwaway dataset)

- The script runs end to end on this Mac: weights load with no shape
  mismatches, validation scores the pretrained model at about 99 % character
  accuracy, and the exported model loads back through
  `penn_ocr.predict --rec-model-dir` and transcribes a crop.
- Training is slow on CPU: roughly 7 s per line image while another OCR job
  was running. A few hundred lines for 10 epochs is an overnight run. A GPU
  machine (or `MODEL=PP-OCRv6_small_rec`) is the practical route.
- The accuracy printed for *training* batches is very low even before any
  weight update, while validation is high. The likely cause is batch
  normalisation running on small, heavily padded batches; this is not yet
  confirmed. Judge runs by the validation metric and by
  `python -m penn_ocr.evaluate --split val`, not by the training readout.
- No result on real human labels exists yet. Whether fine-tuning helps is open.
