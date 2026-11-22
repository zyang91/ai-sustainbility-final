"""Export the numbers the slide deck shows into slides/src/data/*.json.

    python slides/export_data.py      (from the repository root, penn-ocr env)

Everything the deck draws comes from files the pipeline already wrote:
annotation/ (benchmark, evaluation), docs/semantic/ (CSV tables),
work/semantic/ (embeddings map) and docs/demo/data.js (recorded runs).
Three benchmark crops are copied, shrunk to JPEG, into slides/public/img/.
"""
import csv
import difflib
import json
import re
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
OUT = ROOT / "slides" / "src" / "data"
IMG = ROOT / "slides" / "public" / "img"
OUT.mkdir(parents=True, exist_ok=True)
IMG.mkdir(parents=True, exist_ok=True)


def dump(name, obj):
    (OUT / f"{name}.json").write_text(json.dumps(obj, ensure_ascii=False, separators=(",", ":")))
    print(f"{name}.json  {(OUT / f'{name}.json').stat().st_size // 1024} KB")


def rows(path):
    with open(path, newline="") as fh:
        return list(csv.DictReader(fh))


def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return v


# ------------------------------------------------------------- archive
docs = rows(ROOT / "annotation" / "documents.csv")
dump("documents", [dict(id=d["doc_id"], year=int(d["year"]), title=d["title"], status=d["status"],
                        source=d["source"], pages=int(d["n_pages"])) for d in docs])

# ------------------------------------------------------------- OCR examples
truth = {r["sample_id"]: r for r in rows(ROOT / "annotation" / "ground_truth.csv")}
pred = {r["sample_id"]: r for r in map(json.loads, open(ROOT / "work/predictions/paddle_pretrained.jsonl"))}
EXAMPLES = [
    ("1948_physical_dev_report_p0005_b05", "A digit read as a letter"),
    ("1977_landscape_dev_plan_p0015_b00", "A sentence silently lost"),
    ("1966_campus_dev_plan_ua_p0035_b01", "A qualifying clause lost"),
]


def words(t):
    return re.sub(r"\s+", " ", t).strip().split(" ")


examples = []
for sid, label in EXAMPLES:
    ref, hyp = words(truth[sid]["text"]), words(pred[sid]["text"])
    tokens = []
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, ref, hyp, autojunk=False).get_opcodes():
        if tag == "equal":
            tokens.append(["=", " ".join(ref[i1:i2])])
        if tag in ("replace", "delete"):
            tokens.append(["-", " ".join(ref[i1:i2])])
        if tag in ("replace", "insert"):
            tokens.append(["+", " ".join(hyp[j1:j2])])
    im = Image.open(ROOT / "work" / "crops" / f"{sid}.png").convert("L")
    im.thumbnail((1400, 1400))
    im.save(IMG / f"{sid}.jpg", quality=82)
    t = truth[sid]
    examples.append(dict(id=sid, label=label, doc=t["doc_id"], year=int(t["year"]), page=int(t["page"]),
                         split=t["split"], image=f"img/{sid}.jpg", tokens=tokens))
dump("ocr_examples", examples)

# ------------------------------------------------------------- semantic
sem = ROOT / "docs" / "semantic"
dump("theme_by_era", [{k: num(v) for k, v in r.items()} for r in rows(sem / "theme_share_by_era.csv")])
dump("theme_by_plan", [{k: num(v) for k, v in r.items()} for r in rows(sem / "theme_share_by_plan.csv")])
dump("carried", [{k: num(v) for k, v in r.items()} for r in rows(sem / "carried_over_text.csv")])
sim = rows(sem / "plan_similarity.csv")
dump("similarity", dict(plans=[r["plan"] for r in sim],
                        matrix=[[round(float(r[p]), 3) for p in [s["plan"] for s in sim]] for r in sim]))
check = json.loads((ROOT / "annotation" / "semantic_theme_check.json").read_text())["judgements"]
dump("theme_check", {t: sum(v) for t, v in check.items()})

res = json.loads((ROOT / "work" / "semantic" / "results.json").read_text())
meta = [json.loads(line) for line in open(ROOT / "work" / "semantic" / "passages.jsonl")]
from penn_semantic.figures import CLUSTER_NAMES  # noqa: E402

points = []
for (x, y), m, theme, cl in zip(res["tsne"], meta, res["labels"], res["clusters"]["labels"]):
    snippet = re.sub(r"\s+", " ", m["text"]).strip()
    points.append([round(x, 2), round(y, 2), m["era"], res["short"][m["report"]], int(m["page_start"]),
                   theme, int(cl), snippet[:220] + ("…" if len(snippet) > 220 else "")])
dump("tsne", dict(eras=res["eras"], clusters=[CLUSTER_NAMES[k] for k in range(len(CLUSTER_NAMES))],
                  points=points))
dump("clusters_by_era", dict(eras=res["eras"], names=[CLUSTER_NAMES[k] for k in range(len(CLUSTER_NAMES))],
                             share=[[round(res["clusters"]["by_era"][e].get(str(k), 0), 3) for e in res["eras"]]
                                    for k in range(len(CLUSTER_NAMES))]))

# ------------------------------------------------------------- RAG evaluation
dump("rag_eval", [{k: num(v) for k, v in r.items()} for r in rows(ROOT / "annotation" / "rag_eval.csv")])
qs = json.loads((ROOT / "annotation" / "rag_questions.json").read_text())["questions"]
dump("rag_questions", [dict(id=q["id"], kind=q["kind"], question=q["question"]) for q in qs])

demo = (ROOT / "docs" / "demo" / "data.js").read_text()
dump("demo", json.loads(demo[demo.index("{"):demo.rstrip().rstrip(";").rindex("}") + 1]))
