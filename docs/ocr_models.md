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

## Benchmark, second part (Vision 1.4, 2026-11-22)

CER and WER are in the result above. This section adds the secondary
measures, the errors that matter for reading the plans, and cost and speed.

### Dates, numbers and names read exactly

`python -m penn_ocr.entities` finds every date, number, institutional name and
place name in the human reference text, aligns the OCR text to it character
by character, and counts an occurrence as correct only when the aligned OCR
text is identical. Dates and numbers are found by pattern; names come from a
reviewed list (`annotation/ocr_names.json`: 20 institutions and 48 places, for
example "Philadelphia City Planning Commission", "Wharton School", "Locust
Walk", "38th Street"). The bare word "University" is left out. A second level,
`value`, ignores spaces and letter case.

Held-out test partition (33 paragraphs):

| Category | Occurrences | Pretrained exact | Fine-tuned exact |
|---|---|---|---|
| Dates | 5 | 5 | 5 |
| Numbers | 13 | 13 | 13 |
| Institutional names | 5 | 5 | 5 |
| Place names | 44 | 43 | 44 |
| **Total** | **67** | **66 (98.5 %)** | **67 (100 %)** |

All 92 paragraphs, pretrained model only (it was trained on none of them, so
every partition is held out for it):

| Category | Occurrences | Exact | Value |
|---|---|---|---|
| Dates | 22 | 20 | 21 |
| Numbers | 43 | 43 | 43 |
| Institutional names | 29 | 28 | 28 |
| Place names | 79 | 77 | 77 |
| **Total** | **173** | **168 (97.1 %)** | **169 (97.7 %)** |

The five misses:

| Reference | Pretrained OCR | Kind |
|---|---|---|
| 31st Street (test) | 3lst Street | letter l for digit 1 |
| 31st Street (val) | 3lst Street | letter l for digit 1 |
| May 31st (train) | May 3lst | letter l for digit 1 |
| November 3, 1961 (train) | NovEmBER 3,1961 | case and spacing; value right |
| Law School (train) | Law Sohcol | misread letters |

Reading: no number or date was read as a different valid number or date. With
65 occurrences and no such error, the rate of that kind of error is below
about 5 % (the rule of three: 3 / 65), which is as precise as this sample
allows. The fine-tuned model reads "31st" correctly in all three places; the
training lines contained the 1948 "May 31st" line, so this is one corrected
pattern, not a general gain. The difference on test is one occurrence.

Numbers in this ground truth are few because the benchmark samples prose
paragraphs. Tables, where most figures of the plans are, were not sampled
(see 3.3 in `docs/rag_report.md`).

### OCR errors that affect historical interpretation

Every word-level difference between the pretrained OCR and the reference in
the 92 paragraphs (31 differences) was read and sorted by what it does to a
reader or a search.

| Effect | Cases | Examples |
|---|---|---|
| **Text silently lost** | 2 | A clause in the 1966 University Architect copy, p. 35 ("intent or outside direction, be carried out at a lower density"); a sentence in the 1977 Landscape Development Plan, p. 15 ("Beyond the creation of the Green, the report stressed …"). The detector found no text line there. |
| Letter for digit, or digit for letter | 4 | 3lst (three times), wil1 |
| Misread letters in a word | 9 | locaticn, populaticn, cf, Uriversity, thrid, freguently, Laborabory, eguipment, Law Sohcol |
| Spacing, case, joined or split words | 5 | NovEmBER 3,1961; 1961and; numberof; UniversityProperty; Univer sity's; SEAS read as SEAs |
| Punctuation only | 11 | Chinese full stop 。 for a period, a comma read as a period, three dropped dashes, a stray "7" and "/a" |

Of these, only the lost text changes what the plans say. It is also the hardest
to notice: nothing in the transcription shows that a line is missing, and a
lost qualifying clause ("at a lower density") changes the sense of a planning
statement. Lost lines account for most of the remaining test CER (about 62 of
77 character errors).

The other errors leave the meaning readable to a person but break an exact
search for the word. They matter for keyword search, much less for the
embedding search used in Part 2. Across the whole scanned corpus (1.46 million
characters) the patterns found here are rare:

| Pattern in the full corpus | Count | Most frequent |
|---|---|---|
| Letter inside a number | 26 | 196l (4), 38l0 (3), 1l4 (2), 19l3 (1) |
| Digit 1 inside a word | 57 | Pennsy1vania (9), wil1 (8), Counci1 (3), Schuy1kill (3) |
| Ordinal with letter l (3lst) | 3 | all three are the benchmark paragraphs above |
| Chinese full stop for a period | 51 | |

"196l" is a year that a search for 1961 will not find, and "Pennsy1vania" and
"Schuy1kill" are names. These are listed so that a reader of the corpus knows
to expect them; they were not corrected, because the corpus is kept as the
OCR read it.

### Cost and speed

| | Pretrained PP-OCRv6 | Fine-tuned |
|---|---|---|
| Training data | none | 209 line images from 39 paragraphs, typed by hand |
| Training time | none | about 12.5 min for 20 epochs on a Colab T4; about 8 h estimated on this Mac's CPU (56 s × 540 steps) |
| Recognition, benchmark crop (CPU) | 2.40 s | 2.47 s |
| Full corpus, 1,503 scanned pages (CPU, with layout and orientation) | 6.3 h, 15.0 s per page | the same model size, so about the same |
| Money | none | none (Colab free tier) |
| Reproducing it | published weights, version pinned | the training lines, the patched training script and a GPU run; the checkpoint must be archived with the corpus |

The human transcription that both models are measured against took about
5 hours of recorded typing for the first pass of 94 paragraphs (median 2
minutes per paragraph) and 0.5 hours for the 14 blind second passes. That
cost is the benchmark's, not the fine-tuning's, but fine-tuning needs it too.

### Conclusion for 1.4

On the secondary measures the two models agree within one occurrence, as they
do on CER. The fine-tuned model costs a training run and is harder to
reproduce, for no measurable gain on held-out text. The pretrained model stays
the choice for the corpus. The error that most affects historical reading is
not a misread character but a missed line, which neither model addresses
because it happens in detection.

Status: 1.4 is closed (decided 2026-11-22). The remaining errors are few and
mostly in detection; further OCR work would not change any conclusion of the
project, so none is planned. The one open item is the names list
(`annotation/ocr_names.json`), which was reviewed by one person.
