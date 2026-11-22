"""Semantic analysis of the plan corpus (Vision 1.5).

    python -m penn_semantic.embed
    python -m penn_semantic.analyze

Four analyses on the passage embeddings:

1. Themes over time: each passage is assigned to a planning theme by
   similarity to theme descriptions (themes.py); the share of each theme is
   counted per plan and per era. Shares, not counts, because the plans range
   from 25 to 236 passages.
2. Plan similarity: each plan is represented by the mean of its passage
   vectors, after the corpus mean is subtracted; plans are compared by cosine
   similarity.
3. Carried-over text: for every passage, its most similar passage in any
   earlier plan. Above 0.95 the passage is in effect repeated; below 0.80 it
   has no close precedent in the archive.
4. Clusters: k-means on the passage vectors finds groups without the theme
   list; each cluster is described by its most distinctive words (class-based
   TF-IDF) and its share per era. t-SNE places the passages on a map.

Writes work/semantic/results.json and the tables in docs/semantic/.
"""
import csv
import json
import re
from collections import Counter, defaultdict

import numpy as np
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.manifold import TSNE

from . import themes
from .embed import ERAS, OUT, load

from penn_ocr.config import ROOT

DOCS = ROOT / "docs" / "semantic"
K = 12
SEED = 20261122
REPEAT, NOVEL = 0.95, 0.80

SHORT = {  # report -> short label for tables and figures
    "1948_physical_dev_report": "1948 Trustees' report",
    "1961_dev_plan": "1961 Development Plan",
    "1963_dev_plan": "1963 Development Plan",
    "1966_campus_dev_plan": "1966 Development Plan",
    "1977_landscape_dev_plan": "1977 Landscape Plan",
    "1978_framework_campus_planning": "1978 Framework (draft)",
    "1979_campus_dev_plan_interim": "1979 Interim Report (draft)",
    "1981_campus_dev_plan_reports": "1982 Reports",
    "1982_campus_dev_plan_reports": "1983 Reports",
    "1983_campus_dev_plan_reports": "1984 Reports",
    "1987_campus_master_plan_draft": "1987 Master Plan (draft)",
    "1992_master_land_use_plan": "1992 Land Use Plan (draft)",
    "1998_campus_dev_master_plan": "1998 Master Plan (draft)",
    "1998_campus_dev_plan_brief": "1998 Executive Brief",
    "2006_penn_connects": "2006 Penn Connects",
    "2012_penn_connects_2": "2012 Penn Connects 2.0",
    "2018_penn_connects_3": "2018 Penn Connects 3.0",
}


def write(name: str, rows: list[dict]):
    DOCS.mkdir(parents=True, exist_ok=True)
    with open(DOCS / name, "w", newline="") as f:
        w = csv.DictWriter(f, list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def shares(labels, keys, groups) -> dict:
    out = {}
    for g in groups:
        idx = [i for i, k in enumerate(keys) if k == g]
        c = Counter(labels[i] for i in idx)
        out[g] = {t: c[t] / len(idx) for t in c} | {"_n": len(idx)}
    return out


def ctfidf(texts_by_cluster: dict[int, str], top: int = 8) -> dict[int, list[str]]:
    """Words that set each cluster apart from the others."""
    vec = CountVectorizer(stop_words="english", token_pattern=r"(?u)\b[a-zA-Z][a-zA-Z-]{2,}\b",
                          min_df=3, max_df=0.5)
    ids = sorted(texts_by_cluster)
    X = vec.fit_transform([texts_by_cluster[i] for i in ids]).toarray().astype(float)
    tf = X / X.sum(1, keepdims=True)
    idf = np.log(1 + X.sum(1).mean() / X.sum(0))
    w = tf * idf
    vocab = np.array(vec.get_feature_names_out())
    return {c: vocab[np.argsort(-w[k])[:top]].tolist() for k, c in enumerate(ids)}


def main():
    meta, V = load()
    reports = sorted({m["report"] for m in meta}, key=lambda r: (min(x["year"] for x in meta if x["report"] == r), r))
    eras = [e for e, _, _ in ERAS]
    names = list(themes.THEMES) + ["Other"]
    S = themes.scores(V)
    labels = themes.assign(S)

    # 1. themes over time
    by_report = shares(labels, [m["report"] for m in meta], reports)
    by_era = shares(labels, [m["era"] for m in meta], eras)
    write("theme_share_by_plan.csv", [dict(plan=SHORT[r], passages=by_report[r]["_n"],
                                           **{t: round(by_report[r].get(t, 0), 3) for t in names}) for r in reports])
    write("theme_share_by_era.csv", [dict(era=e, passages=by_era[e]["_n"],
                                          **{t: round(by_era[e].get(t, 0), 3) for t in names}) for e in eras])

    # 2. plan similarity
    # centred first: sentence-model vectors share a large common direction, which
    # puts every plan-to-plan cosine between 0.90 and 0.99 and hides the differences
    Vc = V - V.mean(0)
    cent = np.stack([Vc[[i for i, m in enumerate(meta) if m["report"] == r]].mean(0) for r in reports])
    cent /= np.linalg.norm(cent, axis=1, keepdims=True)
    sim = cent @ cent.T
    write("plan_similarity.csv", [dict(plan=SHORT[a], **{SHORT[b]: round(float(sim[i, j]), 3)
                                                          for j, b in enumerate(reports)}) for i, a in enumerate(reports)])

    # 3. carried-over text: nearest passage in any EARLIER plan
    years = np.array([m["year"] for m in meta])
    carry = []
    for r in reports:
        idx = [i for i, m in enumerate(meta) if m["report"] == r]
        y = meta[idx[0]]["year"]
        earlier = np.where(years < y)[0]
        if len(earlier) == 0:
            continue
        best = (V[idx] @ V[earlier].T).max(1)
        src = Counter(meta[earlier[j]]["report"] for j in (V[idx] @ V[earlier].T).argmax(1)[best >= REPEAT])
        carry.append(dict(plan=SHORT[r], passages=len(idx), repeated=round(float((best >= REPEAT).mean()), 3),
                          close=round(float(((best >= NOVEL) & (best < REPEAT)).mean()), 3),
                          new=round(float((best < NOVEL).mean()), 3),
                          repeated_from="; ".join(f"{SHORT[k]} ({v})" for k, v in src.most_common(2))))
    write("carried_over_text.csv", carry)

    # 4. clusters and map
    km = KMeans(n_clusters=K, n_init=10, random_state=SEED).fit(V)
    cl = km.labels_
    words = ctfidf({c: " ".join(meta[i]["text"] for i in range(len(meta)) if cl[i] == c) for c in range(K)})
    centre_ex = {}
    for c in range(K):
        idx = np.where(cl == c)[0]
        d = V[idx] @ (km.cluster_centers_[c] / np.linalg.norm(km.cluster_centers_[c]))
        centre_ex[c] = [meta[idx[j]]["id"] for j in np.argsort(-d)[:3]]
    cl_era = shares(list(cl), [m["era"] for m in meta], eras)
    theme_of = {c: Counter(labels[i] for i in np.where(cl == c)[0]).most_common(2) for c in range(K)}
    xy = TSNE(n_components=2, metric="cosine", init="pca", perplexity=30, random_state=SEED).fit_transform(V)

    res = dict(themes=names, reports=reports, short=SHORT, eras=eras, labels=labels,
               by_report=by_report, by_era=by_era, similarity=sim.round(4).tolist(), carry=carry,
               clusters=dict(k=K, labels=cl.tolist(), words=words, examples=centre_ex,
                             by_era={e: {str(k): v for k, v in d.items()} for e, d in cl_era.items()},
                             theme_mix={c: [(t, n) for t, n in v] for c, v in theme_of.items()},
                             sizes=Counter(cl.tolist())),
               tsne=xy.round(3).tolist(), threshold=themes.THRESHOLD)
    (OUT / "results.json").write_text(json.dumps(res, default=int))
    write("clusters.csv", [dict(cluster=c, passages=int((cl == c).sum()), words=", ".join(words[c]),
                                main_themes="; ".join(f"{t} {n}" for t, n in theme_of[c]),
                                **{e: round(cl_era[e].get(c, 0), 3) for e in eras}) for c in range(K)])
    print(f"{len(meta)} passages, {len(reports)} plans, {K} clusters -> {OUT / 'results.json'}, {DOCS}")


if __name__ == "__main__":
    main()
