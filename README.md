# ai-sustainbility-final

AI for sustainability final project: semantic analysis and AI-assisted
exploration of Penn's historical campus master plans. The full plan is in
[VISION.md](VISION.md). This repository currently covers Part 1 up to the
ground-truth stage.

| Vision step | State |
|---|---|
| 1.1 Archive assembled, metadata recorded | done ([annotation/documents.csv](annotation/documents.csv)) |
| 1.2 Open-source OCR baseline, fine-tuning set-up | baseline runs; fine-tuning waits for ground truth |
| 1.3 Mini human validator, sampling, splits | built; transcription in progress |
| 1.4 Benchmark incl. Claude | not started (`penn_ocr.evaluate` already scores any prediction file) |

## Set-up

    conda create -n penn-ocr python=3.12
    conda activate penn-ocr
    pip install -r requirements.txt

Source PDFs go in `data/<year>/` (not in git). Everything derived from them
(page images, crops, model output) goes in `work/` (not in git). The sample
manifest and the human transcriptions live in `annotation/` and are tracked.

## Pipeline

    python -m penn_ocr.documents          # 1. manifest of the archive
    python -m penn_ocr.page_ocr           # 2. PaddleOCR + layout on sampled pages (about 1 h on CPU)
    python -m penn_ocr.regions            # 3. choose paragraph crops, assign train/val/test
    streamlit run app/validator.py        # 4. type the ground truth
    python -m penn_ocr.groundtruth        # 5. build annotation/ground_truth.csv
    python -m penn_ocr.predict --engine paddle   # 6. baseline predictions on the crops
    python -m penn_ocr.evaluate           # 7. CER / WER on the held-out test partition

Fine-tuning experiment, once enough train and val samples are typed:

    python -m penn_ocr.export_rec         # line images + labels from train/val only
    bash finetune/run_finetune.sh
    python -m penn_ocr.predict --engine paddle --rec-model-dir work/finetune/inference --name paddle_finetuned
    python -m penn_ocr.evaluate --split val

Model versions, licenses and every training setting are in
[docs/ocr_models.md](docs/ocr_models.md).

## How the ground-truth sample is drawn

- **Scans only.** The 17 documents from 1948 to 1998 are scans and are the
  OCR benchmark. Penn Connects (2006, 2012, 2018) is born-digital with its own
  text layer and is left out.
- **Pages.** Ten pages per document, one from each tenth of the document, with
  a fixed seed. The archive cover sheets of the UPJ 9.4 files are skipped.
- **Regions.** Layout blocks labelled as body text with 3 to 12 printed lines.
  Tables, figures, captions and maps are not sampled.
- **Balance.** Six regions per document, at most two per page, spread across
  three scan-quality levels (terciles of baseline OCR confidence, so hard
  crops are not under-represented).
- **Small on purpose.** About 100 paragraphs out of roughly 1,500 scanned
  pages. The queue rotates through the documents, so a partial pass still
  covers every period.

## Train / validation / test separation

Partitions are assigned by **page**: all paragraphs from one page share a
partition, so neighbouring paragraphs never straddle train and test.

One family is split by **document** instead. The 1961, 1963 and 1966
Development Plans are editions of the same text and the archive has two scans
of each, so both 1961 scans are train, both 1963 scans are validation and both
1966 scans are test. The editions still share some wording across partitions;
that residual overlap is a known limit of a small archive.

## The validator

`streamlit run app/validator.py` shows one crop and an empty box.

- No OCR text is loaded or shown. The only model-derived hint is the number of
  printed lines the detector counted, used to check line breaks.
- One typed line per printed line. That alignment is what lets a paragraph
  become line-level training data; the benchmark itself ignores line breaks.
- Flags: unclear characters, illegible text, uncertain transcription, not
  usable. `[?]` marks a character that cannot be read.
- **Second pass**: about 15 % of finished samples come back blank for an
  independent re-typing. **Review & reconcile** shows the two passes side by
  side and saves a reconciled final text.
- Every save appends to `annotation/transcriptions.jsonl`; nothing is
  overwritten, so the benchmark can be audited.

Human transcriptions are the only ground truth. Model output, including
Claude's in step 1.4, is always scored against them and never used as a
reference.
