"""Does OCR error change the embeddings? (Vision 1.5, optional sensitivity test)

    python -m penn_semantic.sensitivity

The 92 benchmark paragraphs exist twice: as typed by a person and as read by
the OCR model chosen for the corpus. Both versions are embedded with the same
model. Measured:
  - cosine similarity between the two versions of each paragraph, against
    the similarity between different paragraphs as a scale;
  - whether the OCR version's closest typed paragraph is its own;
  - whether the two versions get the same theme.
"""
import json

import numpy as np

from penn_ocr import groundtruth, metrics
from penn_ocr.config import PREDICTIONS

from . import themes
from .embed import OUT, encode


def main():
    truth = groundtruth.build()
    ocr = {r["sample_id"]: r["text"] for r in map(json.loads, open(PREDICTIONS / "paddle_pretrained.jsonl"))}
    rows = [t for t in truth if t["sample_id"] in ocr]
    human = encode([metrics.normalize(t["text"]) for t in rows])
    machine = encode([metrics.normalize(ocr[t["sample_id"]]) for t in rows])
    same = (human * machine).sum(1)
    cross = human @ human.T
    others = cross[~np.eye(len(rows), dtype=bool)]
    own = (machine @ human.T).argmax(1) == np.arange(len(rows))
    th = themes.assign(human @ themes.theme_vectors().T)
    tm = themes.assign(machine @ themes.theme_vectors().T)
    cer = np.array([metrics.cer(t["text"], ocr[t["sample_id"]]) for t in rows])
    worst = np.argsort(same)[:5]
    out = dict(
        paragraphs=len(rows),
        cosine_same_paragraph=dict(mean=float(same.mean()), min=float(same.min()),
                                   p5=float(np.percentile(same, 5))),
        cosine_different_paragraphs=dict(mean=float(others.mean()), p99=float(np.percentile(others, 99)),
                                         max=float(others.max())),
        own_paragraph_nearest=int(own.sum()),
        same_theme=int(sum(a == b for a, b in zip(th, tm))),
        theme_changes=[dict(sample_id=rows[i]["sample_id"], human=th[i], ocr=tm[i], cer=round(float(cer[i]), 4))
                       for i in range(len(rows)) if th[i] != tm[i]],
        lowest=[dict(sample_id=rows[i]["sample_id"], cosine=round(float(same[i]), 4), cer=round(float(cer[i]), 4))
                for i in worst],
        corr_cer_cosine=float(np.corrcoef(cer, same)[0, 1]),
    )
    (OUT / "sensitivity.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
