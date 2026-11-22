# Part 2 report: building the research assistant, and its limits

Status on 2026-11-22. This covers Vision 2.1 to 2.4: retrieval, question
answering, the local chatbot, and a small evaluation (18 questions, each asked
three times; section 4).

**Short version.** On questions about one named plan, the answer contained the
right fact in 34 of 39 runs (87%), and the source page was among the passages
the model was given in 37 of 39. Three things fail. A question that assumes
something the plan does not contain was answered with invented figures in 3 of
3 runs. A question about how parking changed across two decades was answered
wrongly in 3 of 3 runs. And a correct answer cited the passage that actually
holds the fact in only 30 of 39 runs. The system shows its sources so that an
answer can be checked, and at present every answer needs to be.

## 1. What was built

```
work/corpus/paragraphs.jsonl          full corpus, one record per text block
        |  penn_rag.passages
work/rag/passages.jsonl               1,754 passages with document, year, pages
        |  penn_rag.index             BAAI/bge-base-en-v1.5 (sentence-transformers)
work/rag/chroma/                      ChromaDB, cosine distance
        |  penn_rag.retrieve          search, filters, per-plan search
        |  penn_rag.answer / agent    llama3.1:8b in Ollama, numbered citations
app/chatbot.py                        Streamlit chat with sources and page images
docs/demo/                            static page replaying six recorded runs
```

Everything runs on one laptop. No text leaves the machine.

## 2. Build process

### 2.1 Corpus to passages

Input is the full-corpus transcription (1,787 pages, 33 PDFs, about 2.0 million
characters). Three decisions shape what the assistant can find.

| Decision | What was done | Why |
|---|---|---|
| Prose only | Blocks flagged `prose` by `penn_ocr.corpus.is_prose` (label, at least 8 words or a short list item ending in a full stop, mostly lower case, OCR confidence at least 0.8) | Map labels, running headers, page numbers and stray marks would otherwise be indexed |
| Human page review | 471 doubtful pages were checked by a person: 447 removed, 11 restored, 13 left as they were | The layout model filed some body text under "image" and kept labels from maps |
| One copy of each plan | The second scans of the 1961, 1963 and 1966 plans are excluded (93 to 99% of their text is in the copy that is kept) | Otherwise the same passage is retrieved twice and those years weigh double |

The analysis set is 17 reports. The sixteen small PDFs of Penn Connects 3.0
(2018) count as one report.

Passages are built by joining neighbouring prose blocks of one document until
a passage reaches about 1,000 characters (hard limit 1,600; a longer block is
split at sentence ends). Joining matters for the born-digital PDFs, where one
bulleted paragraph is often stored as several half sentences. A section
heading starts a new passage and is kept as metadata for two pages, then
dropped, because a missed heading would otherwise label unrelated text.

Each passage records document, report, year, draft or published status,
section heading and page range.

### 2.2 Tables

The first test question, how many parking spaces the 1961 plan projected,
could not be answered: the figures are in a table and tables were not prose.
Tables were then added as passages of their own, rows kept on separate lines,
with the caption printed above them. A block with fewer than six digits is not
treated as a table. This added 50 tables. After the change the same question
returned 3,000 spaces for 1965 and 3,300 for 1970, cited to page 29.

### 2.3 Index and retrieval

- Embeddings: `BAAI/bge-base-en-v1.5`, 768 dimensions, computed in-process
  with sentence-transformers. The section heading is embedded together with
  the passage text, because a passage under "Parking" often never repeats the
  word. The same vectors can be reused for Vision 1.5.
- Store: ChromaDB on disk, cosine distance, metadata filters for year range
  and draft or published status.
- Two search modes. `search` returns the six best passages. `search_by_report`
  takes the two best passages from every plan in range and returns them in
  date order, so a question about change over time is not answered from the
  two longest reports alone.

### 2.4 Answering

The model receives only the retrieved passages, numbered, and is told to cite
those numbers, give the year of each statement, quote figures exactly, mark
inference with "This suggests", and say so when the passages do not answer the
question. The app lists which passages were cited and which were retrieved but
not cited, and can show the original page image for each.

Three ways to ask:

| Mode | How it searches |
|---|---|
| Search once | One search, one answer |
| Compare plans | `search_by_report`, one answer |
| Agent | The model calls a `search_plans` tool, can search again, and chooses a year range |

### 2.5 Changes made after testing

Each of these was a failure seen in a test run with `llama3.1:8b`.

| Problem seen | Change |
|---|---|
| The model added "published plans only" to every search, which hid the 1978, 1979, 1987 and 1992 drafts | Draft or published is set only by the person in the sidebar; the model cannot choose it, and it can narrow the year range but not widen it |
| Long search results were cut off without warning | Ollama's default context window was too small for 30 passages; `num_ctx` is set to 16,384 |
| Asked about "the 1950s to the 1970s", the model searched the 1970s only | The period is read from the question in code, and questions about change over time are routed to one per-plan search with a single answer pass |
| Citations written as "(1961, p. 11)" instead of "[3]" | The prompt gives an example; an answer with no citation is sent back once for rewriting; the parser accepts "[8, p. 42]"; the app warns when an answer cites nothing |
| "The plans mentioned Singapore in the following passages", followed by an unrelated passage | Names in the question that occur in none of the passages are reported to the model as a fact |
| After "the plans do not mention this", the retry instruction was used as a search query | A refusal is recognised and not sent back for rewriting |

One finding behind the Singapore fix is worth recording: similarity scores do
not separate questions the archive can answer from ones it cannot. A search
for "a campus in Singapore" scores 0.63, the same as "bicycle lanes", which
the plans do discuss. A score threshold cannot be used to refuse.

### 2.6 Recorded demo

`docs/demo/` is a static page that replays six saved runs: the searches, the
answer exactly as the model wrote it, the passages, and a line written by a
person saying whether the answer matches its sources. One of the six is kept
because it is wrong. Nothing runs when the page is used.

## 3. Limitations

### 3.1 Answers from the 8B model are not reliable

This is the main limitation.

- **Invented figures.** Asked in the chat interface how many parking spaces
  the 1961 plan called for, the model had the correct table in front of it and
  still wrote column headings and numbers that are not in the document
  ("Faculty 1,200, Students 2,400, Hospital 100"), with its own list of page
  references that did not match. Asked again from the command line it gave the
  correct figures.
- **Misread passages.** In the recorded run on parking policy from the 1960s
  to the 1970s, a passage about housing units for undergraduate men was
  reported as evidence about parking, and the conclusion ("a more
  laissez-faire approach") is in no passage.
- **Run-to-run variation.** Temperature is 0.1, and the same question still
  produced a correct answer and a wrong one on different runs. A single good
  answer is not evidence that the question is handled.
- **Citations are not checked.** The system verifies that a cited number
  exists. It does not verify that the passage supports the sentence. A
  confident sentence with a valid citation can still be wrong.

Results by kind of question, from the hand tests:

| Kind of question | Result |
|---|---|
| A fact from one plan (the objectives of the 1961 plan) | Correct and cited |
| A figure from a table | Sometimes correct, sometimes invented |
| Something the archive does not contain | Correctly declined, after the fix |
| Change across several plans | Follows the plans in date order; quality varies, off-topic passages are sometimes used |
| Draft against published version (the two 1998 documents) | No useful answer |

### 3.2 Retrieval

- **No reranking and no keyword search.** Retrieval is one dense-vector
  lookup. An exact name or number that the embedding does not capture can be
  missed.
- **Retrospective passages answer "when" questions.** Asked when Penn began to
  emphasise pedestrian space, the answer said the 1950s, citing the 1992 plan
  looking back. The archive has no plan from the 1950s. The statement is in a
  source, but it is second-hand, and the 1960s plans that were retrieved were
  not used.
- **Two passages per plan is coarse.** In a comparison, each plan is
  represented by its two closest passages, which may not be its main statement
  on the topic.
- **Successive editions repeat each other.** About 78% of the 1963 plan is
  already in the 1961 plan, and about 71% of the 1966 plan is in the 1963
  plan. They are kept as separate plans on purpose, but a comparison across
  the 1960s will find near-identical text three times.

### 3.3 Corpus and coverage

- **Gaps in time.** Plans exist for 1948, 1961, 1963, 1966, 1977 to 1979, 1982
  to 1984, 1987, 1992, 1998, 2006, 2012 and 2018. Nothing from 1949 to 1960 or
  from 1967 to 1976. A question about the 1950s can only be answered from
  later plans.
- **OCR quality varies by document.** On the held-out benchmark the selected
  model has a character error rate of 0.63%, but that figure comes from 33
  sampled paragraphs. Three documents have clearly lower recognition
  confidence (the 1998 master plan draft at 0.82, the 1978 framework at 0.89,
  the 1992 land use plan at 0.90).
- **Tables are text, not tables.** A table is stored as OCR rows. Column
  alignment is lost, so the model has to work out which number belongs to
  which column. Tables split across pages, and tables the layout model did not
  recognise, are not covered.
- **Maps and drawings are not searchable.** A large share of these plans is
  graphic. Building names and numbers on maps were deliberately left out.
- **Handwriting.** Several scans carry handwritten notes. Pages that were
  mostly handwriting were removed by hand; notes inside a page of body text
  were not treated separately.
- **The prose filter loses some short text.** List items under four words and
  sentence fragments are dropped, an estimated 1 to 2% of the text.

### 3.4 The evaluation is small

Section 4 reports 18 questions. That is enough to show which kinds of
question fail, not to estimate a failure rate with any precision. The source
pages were found by the author with keyword search and have not been checked
by a second person.

### 3.5 The web demo

The demo is a recording, not a deployment. It shows six questions, chosen by
the author, each recorded twice with one run kept. It does not show how the
system behaves on a question it has not seen. The live system cannot be hosted
as a static page: it needs a Python process, the vector store and a local
model.

## 4. Evaluation (Vision 2.4)

### 4.1 Method

`annotation/rag_questions.json` holds 18 questions: 12 facts from one named
plan, 1 figure from a table, 2 about change across decades, and 3 that the
archive cannot answer (two topics that are absent, and one that asks for the
tuition "proposed" by a plan that proposes none). For each answerable question
the page holding the evidence was found by keyword search of the corpus, not
with the retriever under test, and read.

`python -m penn_rag.evaluate --runs 3` asks every question three times through
the agent (54 runs, `llama3.1:8b`, mean 10.8 seconds per answer) and records:

| Measure | Meaning | Checked by |
|---|---|---|
| Retrieval alone | Source page among the six best passages for the question as written, no year filter | code |
| Found | Source page among the passages the model was given | code |
| Fact | Answer contains the expected figure or term | code (pattern) |
| Cited | Answer cites a passage that holds the source page | code |
| Figures grounded | Every number in the answer occurs in a passage it was given | code |
| Declined | For a question the archive cannot answer, the answer says so | code, then read |
| Comparison answers | Whether each statement is supported and placed in the right decade | read by the author |

Every answer is saved in `work/rag/eval_runs.jsonl`; the per-question table is
`annotation/rag_eval.csv`.

### 4.2 Results

Thirteen questions about one named plan (39 runs):

| Measure | Result |
|---|---|
| Retrieval alone, source page in the top six | 10 of 13 questions (first place for 6) |
| Found, with the agent's own year filter | 37 of 39 runs |
| Fact correct | 34 of 39 runs; 11 of 13 questions correct on all three runs |
| Cited the passage that holds the fact | 30 of 39 runs |

Three questions the archive cannot answer (9 runs): 6 declined correctly, 3
invented an answer.

Two questions about change across decades (6 runs), read by the author: 0 of 3
acceptable for parking, 3 of 3 partly supported for pedestrian circulation.

### 4.3 What the failures were

- **Invented tuition (3 of 3 runs).** Asked what tuition the 1961 plan
  proposed, the model answered "$1,250 per year for graduate students", once
  adding "$1,060 for part-time undergraduates". The plan has no tuition
  figures. The numbers are enrolment counts from the table on page 25, given a
  dollar sign. The model did decline the two questions whose subject is absent
  altogether (Singapore, COVID-19); it failed when the question's premise was
  false but the passages contained plausible numbers.
- **The figure check did not catch it.** Because 1,250 does occur in a
  retrieved passage, "figures grounded" passed. That check flagged 3 of 54
  runs and missed the most serious error in the set. Matching numbers is not
  evidence that a sentence is supported.
- **Parking across the 1960s and 1970s (0 of 3).** Every run opened with a
  passage about housing for undergraduate men and drew a conclusion about
  parking from it. Two runs described statements from the 1963 and 1966 plans
  as the position "by the 1970s". The per-plan search returned the 1960s
  parking pages but none of the three 1970s pages identified as evidence.
- **Right answer, wrong citation.** The 1961 campus area (140 acres, 110 more)
  was correct on all three runs and cited a passage from page 2 that does not
  contain it; the passage that does was first in the list. The Sansom Common
  answer was correct but drew on the draft master plan while attributing
  everything to the Executive Brief.
- **Woodland Avenue (0 of 3 on the pattern, 1 of 3 on reading).** The right
  passage was retrieved first. Two runs said the 1992 plan "did not mention
  any changes to Woodland Avenue". The third said the same and then, in the
  next sentence, gave the 1957 closing correctly.
- **An ambiguous question.** "What student density per acre did the 1966 plan
  use?" has two answers in the plan: 150 students per acre for undergraduate
  housing (the one marked as gold) and 250 people per acre for graduate
  apartments. Two runs gave the second. This is a fault in the question, and
  it is counted as wrong above.
- **Citing everything.** On the pedestrian question one run cited 7 of 25
  passages, another listed the range [1] to [6] after a single sentence. A
  citation list of that kind cannot be used to check a claim.

Retrieval without a year filter missed three questions. One was the 1966
density sentence, which also appears word for word in the 1963 edition; one
was ranked 13th (1948); one was not in the top twenty (1978). In all three the
agent found the page once it restricted the search to the year named in the
question.

### 4.4 A defect found by the evaluation

In the first full run the Woodland Avenue question was refused on all three
runs although the passage was retrieved. The cause was in this project's code:
when an answer had no citation numbers, the model was asked to rewrite it, and
it treated that instruction as a search request, searched for the word
"citations", and reported that the plans did not cover the question. The
rewrite step no longer offers the search tool and keeps the first answer if
the rewrite is no better. The results in 4.2 are from the run after this fix;
the first run is kept in `work/rag/eval_first_run.csv`.

## 5. What would reduce these limits

In order of expected effect:

1. **Have a second person confirm the source pages** in
   `annotation/rag_questions.json`, and add questions of the kinds that failed
   (false premises, comparisons), so that a change can be measured.
2. **Try a larger local model.** The machine has 34 GB of memory and can run a
   12B to 14B model. The retrieval side would not change. This was considered
   and left out of the project's scope: the aim here is a working, documented
   prototype with its limits stated, not the best answer quality a local model
   can reach.
3. **Check citations with more than number matching.** The evaluation shows
   that a figure can occur in the cited passage and still be misreported.
   A second model pass that asks "does this passage state this sentence?"
   would be needed.
4. **Answer plan by plan** for comparison questions: one short, cited
   statement per plan, then a summary. Each step gives the model two passages
   instead of thirty.
5. **Add keyword search** beside the vector search, for names and numbers.
6. **Structured tables**: re-read the 50 tables with a table-recognition model
   so that rows and columns are explicit.

## 6. Reproducing

```
python -m penn_ocr.corpus          # corpus with page decisions and prose flags
python -m penn_rag.passages        # 1,754 passages (50 tables)
python -m penn_rag.index           # ChromaDB in work/rag/chroma/
ollama pull llama3.1:8b
streamlit run app/chatbot.py

python -m penn_rag.retrieve "parking policy" --from 1960 --to 1970 --by-report
python -m penn_rag.agent "How many parking spaces did the 1961 plan project for 1970?"
python -m penn_rag.evaluate --runs 3     # section 4; about 10 minutes
```

Versions used: sentence-transformers 6.3.0, chromadb 1.5.9, Ollama 0.40.17,
`llama3.1:8b`, `BAAI/bge-base-en-v1.5`. Settings are in `penn_rag/config.py`.
