"""Human transcription store.

`annotation/transcriptions.jsonl` is an append-only log: every save adds a
line, nothing is edited in place, so the benchmark stays auditable. The latest
record per (sample, pass) wins. Passes:
  first  - the annotator's blind transcription
  second - an independent blind re-transcription of a subset (error detection)
  final  - a reconciled text entered after comparing first and second
"""
import csv
import json
from datetime import datetime, timezone

from .config import SAMPLE_LINES, SAMPLES_CSV, TRANSCRIPTIONS

FLAGS = {
    "unclear": "Unclear characters",
    "illegible": "Illegible text",
    "uncertain": "Uncertain transcription",
    "unusable": "Not usable (table, figure, handwriting or bad crop)",
}


def samples() -> list[dict]:
    if not SAMPLES_CSV.exists():
        return []
    with open(SAMPLES_CSV) as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        for k in ("order", "year", "page", "x0", "y0", "x1", "y1", "rotation", "n_lines"):
            r[k] = int(r[k])
    return rows


def sample_lines() -> dict:
    return json.loads(SAMPLE_LINES.read_text()) if SAMPLE_LINES.exists() else {}


def clean(text: str) -> str:
    """Keep the typed characters and line breaks; drop only stray whitespace."""
    lines = [ln.rstrip() for ln in text.replace("\r\n", "\n").replace("\r", "\n").split("\n")]
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    return "\n".join(lines)


def save(sample_id: str, text: str, pass_: str = "first", flags=(), notes: str = "",
         annotator: str = "", seconds: float | None = None) -> dict:
    rec = dict(sample_id=sample_id, **{"pass": pass_}, text=clean(text),
               flags=sorted(flags), notes=notes.strip(), annotator=annotator.strip(),
               seconds=None if seconds is None else round(seconds, 1),
               saved_at=datetime.now(timezone.utc).isoformat(timespec="seconds"))
    TRANSCRIPTIONS.parent.mkdir(exist_ok=True)
    with open(TRANSCRIPTIONS, "a") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return rec


def latest() -> dict[str, dict[str, dict]]:
    """{sample_id: {pass: latest record}}"""
    out: dict[str, dict[str, dict]] = {}
    if TRANSCRIPTIONS.exists():
        with open(TRANSCRIPTIONS) as f:
            for line in f:
                if line.strip():
                    rec = json.loads(line)
                    out.setdefault(rec["sample_id"], {})[rec["pass"]] = rec
    return out


def reference(passes: dict[str, dict]) -> dict | None:
    """The record that counts as ground truth for a sample."""
    return passes.get("final") or passes.get("first")
