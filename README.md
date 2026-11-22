# ai-sustainbility-final

AI for sustainability final project: semantic analysis and AI-assisted
exploration of Penn's historical campus master plans. The full plan is in
[VISION.md](VISION.md). Parts 1 and 2 are done.

| Vision step | State |
|---|---|
| 1.1 Archive assembled, metadata recorded | done ([annotation/documents.csv](annotation/documents.csv)) |
| 1.2 Open-source OCR baseline, fine-tuning | done; fine-tuning ties the pretrained model on test, so the pretrained model is used (`docs/ocr_models.md`) |
| 1.3 Mini human validator, sampling, splits | done; 92 usable paragraphs, 14 double-keyed, mismatched lines checked |
| 1.4 OCR benchmark | done: CER/WER, exact match of dates, numbers and names, interpretation-affecting errors, cost and speed (`docs/ocr_models.md`) |
| Full-corpus transcription | done: 1,787 pages; 471 doubtful pages reviewed by hand; prose blocks flagged |
| 1.5 Semantic analysis | done: themes, clusters, plan similarity, carried-over text, OCR sensitivity ([docs/semantic_report.md](docs/semantic_report.md)) |
| 2.1-2.3 Retrieval, answering, local chatbot | done (`penn_rag/`, `app/chatbot.py`, recorded demo in `docs/demo/`) |
| 2.4 Retrieval and answer evaluation | done on 18 questions; results and limits in [docs/rag_report.md](docs/rag_report.md) |

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

Full-corpus transcription with the selected (pretrained) model:

    python -m penn_ocr.page_ocr --all     # every page of the 17 scans, about 6 h on CPU, resumable
    python -m penn_ocr.corpus             # paragraphs.jsonl + one .txt per document in work/corpus/

Page review, for the pages where the automatic result is doubtful (text the
layout model filed under a figure, pages with little or no text, low
confidence). One click per page; decisions are logged in
`annotation/page_checks.jsonl` and applied the next time the corpus is built:

    streamlit run app/page_review.py
    python -m penn_ocr.corpus             # rebuild with the page decisions applied

Each block in `paragraphs.jsonl` carries a `prose` flag: true for running
sentences, false for titles, headers, tables, map labels and low-confidence
fragments. The semantic analysis reads only the prose blocks.

The 2006-2018 plans are born-digital; `penn_ocr.corpus` reads their text
layer directly instead of running OCR.

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
- **Check mismatched lines** (used after the blind passes): the second pass
  showed that two human typings of the same paragraph disagree at about 0.7 %
  CER, as much as the OCR baseline disagrees with a human. This mode lists only
  the printed lines where the typed text differs from the second typing or from
  the baseline OCR, shows the line image, and the annotator decides. It is the
  one place where model output is shown. Consequences, stated plainly: lines
  where human and OCR agree were not re-read, so a shared error survives, and
  the corrected ground truth leans slightly towards the baseline model. Every
  decision is logged in `annotation/line_checks.jsonl`.
- Every save appends to `annotation/transcriptions.jsonl`; nothing is
  overwritten, so the benchmark can be audited.

Human transcriptions are the only ground truth. Model output is always
scored against them and never used as a reference.

## Part 2: research assistant

A local, source-grounded chatbot over the corpus (`penn_rag/`, `app/chatbot.py`).

    python -m penn_rag.passages           # prose blocks -> about 1,700 passages with document, year, pages
    python -m penn_rag.index              # sentence-transformers vectors -> ChromaDB in work/rag/chroma/
    ollama pull llama3.1:8b               # the local language model (needs Ollama running)
    streamlit run app/chatbot.py

- **Passages.** Only prose blocks; second scans of the same plan are left out.
  Neighbouring blocks are joined to about 1,000 characters and keep their
  section heading, source PDF and page range.
- **Retrieval.** `BAAI/bge-base-en-v1.5` vectors in ChromaDB, with filters for
  plan year and draft/final status. "Compare plans" takes the best passages
  from every plan in range, so long reports do not crowd out short ones.
- **Answering.** The model sees only numbered passages and must cite them;
  the app lists cited and uncited sources and can show the original page.
  In agent mode the model chooses its own searches and year ranges.
- Without Ollama the app still searches and shows passages, with no answer.

### Recorded web demo

`docs/demo/` is a static page (plain HTML, CSS and JavaScript, no backend) that
replays six saved runs of the assistant: the searches, the answer as the model
wrote it, the cited passages, and a line written by a person saying whether
the answer matches its sources. One of the six is kept because it is wrong.
Nothing runs when the page is used, so it can be hosted on GitHub Pages
(Settings, Pages, deploy from the `main` branch, folder `/docs`; the page is
then at `/demo/`).

    python3 -m http.server 8520 --directory docs/demo     # view it locally

The recordings live in `docs/demo/data.js`. Passages the answers cite are
included in full; other retrieved passages are cut to about 320 characters.

## Semantic analysis (Vision 1.5)

    python -m penn_semantic.embed          # passage embeddings (same model as retrieval)
    python -m penn_semantic.analyze        # themes, clusters, plan similarity, carried-over text
    python -m penn_semantic.figures        # docs/semantic/*.png
    python -m penn_semantic.sensitivity    # does OCR error change the embeddings?

Findings, method and limits: [docs/semantic_report.md](docs/semantic_report.md).

## Presentation

`slides/` is an interactive slide deck (Vite, React, TypeScript): 17 slides
that follow the project in order, from the archive through OCR, corpus and
semantic analysis to the assistant and its evaluation. Charts respond to hover
and clicks, the OCR examples show the scan beside the text, and the recorded
assistant runs can be replayed with their citations.

    python slides/export_data.py          # numbers and images from the pipeline's outputs -> slides/src/data/
    cd slides && npm install && npm run dev       # http://localhost:8521
    npm run build                         # static copy in slides/dist/, works from any folder

Arrow keys or space step through each slide; `f` is full screen; the dots and
section names at the bottom jump to any slide. The deck has three looks, each a
reproduction of the archive: **Folder** (typed sheets in an archive folder),
**Blueprint** (diazo planning drawings) and **Print** (a 1960s development plan).
Switch with the buttons at the bottom or the `t` key; the choice is remembered.
