"""Targeted check of the human transcriptions (after the blind passes are done).

Typing a paragraph twice showed that two human passes disagree about as often
as the OCR baseline disagrees with a human. Re-reading every line is slow, so
this module lists only the printed lines where the human text differs from
another reading of the same line: the annotator's own second pass, or the
baseline OCR. The annotator looks at the line image and decides.

Every decision is appended to `annotation/line_checks.jsonl`, so it stays
visible which ground-truth lines were touched after seeing model output.
"""
import difflib
import json
from datetime import datetime, timezone

from . import store
from .config import ANNOTATION, PREDICTIONS
from .metrics import normalize

CHECKS = ANNOTATION / "line_checks.jsonl"
BASELINE = PREDICTIONS / "paddle_pretrained.jsonl"
SOURCES = {"second": "Your second typing", "ocr": "OCR"}


def predictions() -> dict[str, list[str]]:
    if not BASELINE.exists():
        return {}
    with open(BASELINE) as f:
        return {r["sample_id"]: r["lines"] for r in map(json.loads, f)}


def checked() -> set[str]:
    if not CHECKS.exists():
        return set()
    with open(CHECKS) as f:
        return {k for line in f if line.strip() for k in json.loads(line)["keys"]}


def record(sample_id: str, keys: list[str], decision: str, before: str, after: str,
           annotator: str = "") -> None:
    rec = dict(sample_id=sample_id, keys=keys, decision=decision, before=before, after=after,
               annotator=annotator.strip(),
               saved_at=datetime.now(timezone.utc).isoformat(timespec="seconds"))
    with open(CHECKS, "a") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def _ratio(a: str, b: str) -> float:
    return difflib.SequenceMatcher(None, a, b, autojunk=False).ratio()


def align(mine: list[str], other: list[str]) -> list[tuple[int | None, int]]:
    """Pairs (my line index, other line index) whose text differs.

    (None, j): the other reading has a line with no counterpart in mine, which
    is what a skipped line looks like. Lines of mine that the other reading
    lacks are not reported: there is nothing to compare them with.
    """
    a, b = [normalize(x) for x in mine], [normalize(x) for x in other]
    out = []
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if op == "equal":
            continue
        left = list(range(j1, j2))
        for i in range(i1, i2):
            best = max(left, key=lambda j: _ratio(a[i], b[j]), default=None)
            if best is not None and _ratio(a[i], b[best]) >= 0.6:
                out.append((i, best))
                left.remove(best)
        out += [(None, j) for j in left if len(b[j]) >= 4]     # ignore stray marks
    return out


def issues(samples: list[dict], log: dict, preds: dict[str, list[str]]) -> list[dict]:
    """Open checks in queue order, one per printed line (or per paragraph)."""
    done, out = checked(), []
    for s in samples:
        sid = s["sample_id"]
        ref = store.reference(log.get(sid, {}))
        if not ref or "unusable" in ref["flags"] or not ref["text"]:
            continue
        mine = ref["text"].split("\n")
        readings = {}
        if "second" in log[sid]:
            readings["second"] = log[sid]["second"]["text"].split("\n")
        if sid in preds:
            readings["ocr"] = preds[sid]
        per_line, missing = {}, []
        for src, other in readings.items():
            if normalize(" ".join(mine)) == normalize(" ".join(other)):
                continue
            if len(mine) != s["n_lines"]:
                # typed line breaks do not follow the print: compare the paragraph
                key = f"{sid}|{src}|P|{normalize(' '.join(other))}"
                if key not in done:
                    per_line.setdefault(None, []).append((src, " ".join(other), key))
                continue
            for i, j in align(mine, other):
                key = f"{sid}|{src}|{normalize(other[j])}"
                if key in done:
                    continue
                if i is None:
                    missing.append((src, other[j], key))
                else:
                    per_line.setdefault(i, []).append((src, other[j], key))
        for i, alts in sorted(per_line.items(), key=lambda kv: -1 if kv[0] is None else kv[0]):
            out.append(dict(sample_id=sid, kind="paragraph" if i is None else "line", line=i,
                            mine=" ".join(mine) if i is None else mine[i], alts=alts))
        for alt in missing:
            out.append(dict(sample_id=sid, kind="missing", line=None, mine=ref["text"], alts=[alt]))
    return out
