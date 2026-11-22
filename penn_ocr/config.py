"""Paths and constants shared by every step."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"                      # source PDFs (git-ignored)
WORK = ROOT / "work"                      # derived images / predictions (git-ignored)
PAGES = WORK / "pages"                    # orientation-corrected page images
PAGE_OCR = WORK / "page_ocr"              # page-level PaddleOCR + layout output
CROPS = WORK / "crops"                    # paragraph crops shown in the validator
PREDICTIONS = WORK / "predictions"        # per-engine predictions on the crops
CORPUS = WORK / "corpus"                  # full-corpus text (Vision 1.1 / 1.5 input)
REC_DATASET = WORK / "rec_dataset"        # line-level export for fine-tuning

ANNOTATION = ROOT / "annotation"          # tracked in git
DOCUMENTS_CSV = ANNOTATION / "documents.csv"
SAMPLES_CSV = ANNOTATION / "samples.csv"
SAMPLE_LINES = ANNOTATION / "sample_lines.json"   # line boxes only, no text
TRANSCRIPTIONS = ANNOTATION / "transcriptions.jsonl"  # append-only human log
GROUND_TRUTH_CSV = ANNOTATION / "ground_truth.csv"
PAGE_CHECKS = ANNOTATION / "page_checks.jsonl"    # append-only page review log

DPI = 200
SEED = 20261114
