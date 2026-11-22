"""Secondary OCR measures (Vision 1.4): are dates, numbers, institutional
names and place names read exactly?

    python -m penn_ocr.entities --candidates     # list name candidates for review
    python -m penn_ocr.entities                  # score every prediction file

CER treats every character alike, but a historian reading the corpus cares
most about a few kinds of token: a year, a count of parking spaces, the name
of a committee or a street. One wrong digit in "1,342,900" costs one character
of CER and makes the figure wrong.

How the measure works:
  - Each occurrence is found in the human reference text. Dates and numbers
    are found by pattern. Names come from a reviewed list,
    annotation/ocr_names.json: candidates were extracted by pattern from the
    ground truth (`--candidates`), and a person kept the real names and gave
    each a type.
  - The reference and the OCR text are aligned character by character, and
    the occurrence counts as correct only when the aligned stretch of OCR text
    is identical (after the same normalisation as CER). A name read correctly
    somewhere else in the paragraph does not count.
  - Line-end hyphenation is joined on both sides first ("Penn-" + "sylvania"),
    because the print splits words that the OCR reads correctly.
  - Two levels are reported. `exact`: identical text. `value`: identical once
    spaces and letter case are ignored ("November 3,1961" has the right value
    but a missing space). A letter read for a digit ("3lst") fails both.

Writes annotation/ocr_entity_scores.csv and work/predictions/entity_errors.jsonl
(every occurrence that was not read exactly, with the OCR text in its place).
"""
import argparse
import csv
import difflib
import json
import re
from collections import Counter, defaultdict

from . import groundtruth, metrics
from .config import ANNOTATION, PREDICTIONS

NAMES = ANNOTATION / "ocr_names.json"
SCORES = ANNOTATION / "ocr_entity_scores.csv"
ERRORS = PREDICTIONS / "entity_errors.jsonl"

MONTH = (r"(?:January|February|March|April|May|June|July|August|September|October|November|December"
         r"|Jan\.|Feb\.|Mar\.|Apr\.|Aug\.|Sept?\.|Oct\.|Nov\.|Dec\.)")
DATE = re.compile(
    rf"{MONTH}\s+\d{{1,2}}(?:st|nd|rd|th)?,?\s+(?:18|19|20)\d\d"      # May 3, 1948
    rf"|{MONTH},?\s+(?:18|19|20)\d\d"                                   # March 1961
    rf"|{MONTH}\s+\d{{1,2}}(?:st|nd|rd|th)?\b"                          # May 3rd
    r"|\b(?:18|19|20)\d\d\s*-\s*(?:\d\d|(?:18|19|20)\d\d)\b"           # 1960-61, 1965-1970
    r"|\b(?:18|19|20)\d0'?s\b"                                          # 1960s
    r"|\b(?:18|19|20)\d\d\b")                                           # 1961
NUMBER = re.compile(r"\$?\d[\d,]*(?:\.\d+)?%?")
# candidate names: capitalised runs, joined by of / the / and / for
CAP = r"(?:[A-Z][a-zA-Z.'&-]*|\d+(?:st|nd|rd|th))"
RUN = re.compile(rf"{CAP}(?:\s+(?:of|the|and|for|on|in)\s+{CAP}|\s+{CAP})*")
INSTITUTION_WORDS = re.compile(
    r"\b(University|College|School|Commission|Committee|Authority|Corporation|Hospital|Museum|"
    r"Department|Board|Council|Trustees|Institute|Library|Center|Office|Association|Foundation|"
    r"Society|Agency|Administration|Company|Bureau|Laboratory|Laboratories)\b")
PLACE_WORDS = re.compile(
    r"\b(Street|Streets|Avenue|Walk|Square|Boulevard|Road|Drive|Expressway|River|Park|Field|"
    r"Green|Station|Bridge|Plaza|Hall|Quadrangle|Philadelphia|City|Schuylkill|Building|"
    r"Gymnasium|Palestra|House|Houses|Tower|Towers|Garden|Gardens|Lane)\b")


def prepare(text: str) -> str:
    """The CER normalisation, plus line-end hyphens joined."""
    return re.sub(r"(?<=[a-z])- (?=[a-z])", "", metrics.normalize(text))


def load_names() -> dict[str, str]:
    """{name: "institution" | "place"} from the reviewed list."""
    if not NAMES.exists():
        return {}
    return {n["name"]: n["type"] for n in json.loads(NAMES.read_text())["names"]}


def find(text: str, names: dict[str, str]) -> list[tuple[str, int, int, str]]:
    """(category, start, end, string) for every occurrence in a reference text."""
    out, taken = [], []
    # names first, longest first, so "38th Street" is a place and not a number
    for name in sorted(names, key=len, reverse=True):
        for m in re.finditer(rf"(?<![\w]){re.escape(name)}(?![\w])", text):
            if not any(a < m.end() and m.start() < b for a, b in taken):
                out.append((names[name], m.start(), m.end(), name))
                taken.append((m.start(), m.end()))
    for m in DATE.finditer(text):
        if not any(a < m.end() and m.start() < b for a, b in taken):
            out.append(("date", m.start(), m.end(), m.group()))
            taken.append((m.start(), m.end()))
    for m in NUMBER.finditer(text):
        s = m.group().rstrip(",.")
        if not any(a < m.start() + len(s) and m.start() < b for a, b in taken):
            out.append(("number", m.start(), m.start() + len(s), s))
            taken.append((m.start(), m.start() + len(s)))
    return sorted(out, key=lambda o: o[1])


def aligned(ref: str, hyp: str):
    """A function mapping a reference span to the OCR text aligned with it."""
    ops = difflib.SequenceMatcher(None, ref, hyp, autojunk=False).get_opcodes()

    def to_hyp(i: int, start: bool) -> int:
        for tag, i1, i2, j1, j2 in ops:
            if i1 <= i < i2 or (not start and i1 < i <= i2):
                if tag == "equal":
                    return j1 + (i - i1)
                return j1 if start else j2
        return len(hyp)

    return lambda a, b: hyp[to_hyp(a, True):to_hyp(b, False)]


def score(ref: str, hyp: str, names: dict[str, str]) -> list[dict]:
    ref, hyp = prepare(ref), prepare(hyp)
    span = aligned(ref, hyp)
    out = []
    for cat, a, b, s in find(ref, names):
        got = span(a, b).strip()
        squash = lambda x: re.sub(r"\s", "", x).casefold()
        out.append(dict(category=cat, ref=s, ocr=got, ok=got == s, value=squash(got) == squash(s),
                        context=ref[max(0, a - 50):b + 50], ocr_context=None if got == s else
                        span(max(0, a - 50), min(len(ref), b + 50))))
    return out


def candidates(rows: list[dict]):
    """Capitalised runs with an institution or place word, for review."""
    c = Counter()
    for r in rows:
        for m in RUN.finditer(prepare(r["text"])):
            s = m.group().strip(" .,'-")
            if INSTITUTION_WORDS.search(s) or PLACE_WORDS.search(s):
                c[s] += 1
    for s, n in sorted(c.items(), key=lambda kv: (-kv[1], kv[0])):
        kind = "institution" if INSTITUTION_WORDS.search(s) else "place"
        print(f"{n:3d}  {kind:11s}  {s}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidates", action="store_true")
    args = ap.parse_args()
    rows = groundtruth.build()
    if args.candidates:
        return candidates(rows)
    names = load_names()
    if not names:
        raise SystemExit(f"No reviewed name list at {NAMES}. Run with --candidates first.")
    truth = {r["sample_id"]: r for r in rows}
    cats = ["date", "number", "institution", "place"]
    table, errors = [], []
    for f in sorted(PREDICTIONS.glob("paddle_*.jsonl")):
        preds = {r["sample_id"]: r for r in map(json.loads, open(f))}
        for split in ("test", "val", "train", "all"):
            tally = defaultdict(lambda: [0, 0, 0])
            for sid, t in truth.items():
                if split != "all" and t["split"] != split or sid not in preds:
                    continue
                for o in score(t["text"], preds[sid]["text"], names):
                    tally[o["category"]][0] += 1
                    tally[o["category"]][1] += o["ok"]
                    tally[o["category"]][2] += o["value"]
                    if not o["ok"] and split != "all":
                        errors.append(dict(engine=f.stem, sample_id=sid, doc_id=t["doc_id"],
                                           split=t["split"], **o))
            for cat in cats + ["total"]:
                n, ok, val = [sum(v[k] for v in tally.values()) for k in range(3)] \
                    if cat == "total" else tally[cat]
                table.append(dict(engine=f.stem, split=split, category=cat, occurrences=n,
                                  exact=ok, value=val, exact_rate=round(ok / n, 4) if n else "",
                                  value_rate=round(val / n, 4) if n else ""))
    with open(SCORES, "w", newline="") as fh:
        w = csv.DictWriter(fh, list(table[0]))
        w.writeheader()
        w.writerows(table)
    with open(ERRORS, "w") as fh:
        for e in errors:
            fh.write(json.dumps(e, ensure_ascii=False) + "\n")
    print(f"{'engine':18s} {'split':5s} " + " ".join(f"{c:>17s}" for c in cats + ["total"]))
    for eng in sorted({t['engine'] for t in table}):
        for split in ("test", "val", "train", "all"):
            cells = {t["category"]: t for t in table if t["engine"] == eng and t["split"] == split}
            print(f"{eng[7:]:18s} {split:5s} " + " ".join(
                f"{cells[c]['exact']:>6d}/{cells[c]['occurrences']:<4d} {100 * (cells[c]['exact_rate'] or 0):5.1f}%"
                for c in cats + ["total"]))
    print(f"-> {SCORES}; {len(errors)} misses -> {ERRORS}")


if __name__ == "__main__":
    main()
