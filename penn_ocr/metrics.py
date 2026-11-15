"""CER / WER against human ground truth.

Both sides get the same light normalisation, so the scores measure reading
errors rather than typography the annotator cannot type consistently:
Unicode NFKC, curly quotes and long dashes mapped to ASCII, line breaks and
runs of whitespace collapsed to one space. Case, punctuation, digits and
line-end hyphens are all kept.
"""
import re
import unicodedata

import jiwer

_MAP = str.maketrans({"‘": "'", "’": "'", "“": '"', "”": '"',
                      "–": "-", "—": "--", "­": "-", "•": "o"})


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKC", text).translate(_MAP)
    return re.sub(r"\s+", " ", text).strip()


def cer(ref: str, hyp: str) -> float:
    return jiwer.cer(normalize(ref), normalize(hyp)) if normalize(ref) else float("nan")


def wer(ref: str, hyp: str) -> float:
    return jiwer.wer(normalize(ref), normalize(hyp)) if normalize(ref) else float("nan")


def corpus(pairs: list[tuple[str, str]]) -> dict:
    """Micro-averaged scores: total errors / total reference length."""
    pairs = [(normalize(r), normalize(h)) for r, h in pairs if normalize(r)]
    if not pairs:
        return dict(n=0, cer=float("nan"), wer=float("nan"))
    refs, hyps = [r for r, _ in pairs], [h if h else " " for _, h in pairs]
    return dict(n=len(pairs), cer=jiwer.cer(refs, hyps), wer=jiwer.wer(refs, hyps))
