"""Fluency score for every corpus block: does it read as English?

The rule filter in `corpus.is_prose` looks only at form (label, word count,
capitals, OCR confidence). This step adds a language-model view: the mean
negative log-likelihood per token under GPT-2 small. Running sentences score
low; garbled OCR, stitched-together map labels and code-like fragments score
high. It judges readability only, never topic, so it does not pre-select the
themes that the semantic analysis is meant to find.

    python -m penn_ocr.corpus      # writes paragraphs.jsonl
    python -m penn_ocr.fluency     # scores the blocks -> work/corpus/fluency.jsonl
    python -m penn_ocr.corpus      # rebuild: adds the score as the `fluency` field

Result (2026-11-15): the score is recorded but NOT used as a filter. Checked
against 94 human-typed paragraphs and the pages a person deleted in the page
review, it does not separate junk from prose once the rule filter has run:
- blocks the rules keep and the model dislikes (score > 6) are mostly good
  text: sentence fragments, bullet items, a sentence with one OCR typo.
  3 of the 94 human-typed paragraphs score above 5.5;
- blocks the rules drop and the model likes are mostly running headers and
  all-capital titles, which are predictable because they repeat;
- on the deleted pages only 6 blocks (381 characters) pass the rules at all,
  so there was little left for a second filter to catch.
Truly garbled blocks (handwriting read as words) do sit at the top of the
score range, but only about ten of them, mixed with good text.

Scores are cached by text hash, so a rebuild only scores new text.
"""
import hashlib
import json

from .config import CORPUS

MODEL = "openai-community/gpt2"
SCORES = CORPUS / "fluency.jsonl"
MAX_TOKENS = 256        # the start of a block is enough to judge it
MIN_TOKENS = 4          # shorter than this there is nothing to score
BATCH = 32


def key(text: str) -> str:
    return hashlib.sha1(text.encode()).hexdigest()[:16]


def load() -> dict[str, float | None]:
    if not SCORES.exists():
        return {}
    with open(SCORES) as f:
        return {r["key"]: r["nll"] for r in map(json.loads, f)}


def score(texts: list[str]) -> list[float | None]:
    """Mean per-token negative log-likelihood of each text (None if too short)."""
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    tok = AutoTokenizer.from_pretrained(MODEL)
    tok.pad_token = tok.eos_token
    model = AutoModelForCausalLM.from_pretrained(MODEL).eval()
    out: list[float | None] = [None] * len(texts)
    order = sorted(range(len(texts)), key=lambda i: len(texts[i]))    # similar lengths together
    for start in range(0, len(order), BATCH):
        idx = order[start:start + BATCH]
        enc = tok([texts[i] for i in idx], return_tensors="pt", padding=True,
                  truncation=True, max_length=MAX_TOKENS)
        with torch.no_grad():
            logits = model(**enc).logits
        nll = torch.nn.functional.cross_entropy(
            logits[:, :-1].transpose(1, 2), enc.input_ids[:, 1:], reduction="none")
        mask = enc.attention_mask[:, 1:]
        n = mask.sum(1)
        mean = (nll * mask).sum(1) / n.clamp(min=1)
        for i, m, k in zip(idx, mean.tolist(), n.tolist()):
            out[i] = round(m, 4) if k + 1 >= MIN_TOKENS else None
        if (start // BATCH) % 25 == 0:
            print(f"  {min(start + BATCH, len(order))}/{len(order)}", flush=True)
    return out


def main():
    have = load()
    texts = {}
    with open(CORPUS / "paragraphs.jsonl") as f:
        for r in map(json.loads, f):
            if key(r["text"]) not in have:
                texts[key(r["text"])] = r["text"]
    print(f"{len(texts)} blocks to score ({len(have)} cached), model {MODEL}", flush=True)
    if texts:
        keys = list(texts)
        with open(SCORES, "a") as f:
            for k, s in zip(keys, score([texts[k] for k in keys])):
                f.write(json.dumps(dict(key=k, nll=s)) + "\n")
    print(f"scores -> {SCORES}")


if __name__ == "__main__":
    main()
