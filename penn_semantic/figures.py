"""Figures for the semantic analysis (docs/semantic/*.png).

    python -m penn_semantic.figures

Colours follow one rule per job: magnitude is a single blue ramp, the plan
similarity (which can be negative after centring) is blue/red around a grey
zero, and the passage map highlights one era at a time in blue over grey,
because six era hues on one scatter cannot be told apart reliably. Every
figure has its numbers in a CSV beside it in docs/semantic/.
"""
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm  # noqa: E402

from .analyze import DOCS  # noqa: E402
from .embed import OUT  # noqa: E402

SURFACE, INK, INK2, MUTED, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#8a8984", "#e7e6e2"
BLUE = ["#cde2fb", "#b7d3f6", "#9ec5f4", "#86b6ef", "#6da7ec", "#5598e7", "#3987e5",
        "#2a78d6", "#256abf", "#1c5cab", "#184f95", "#104281", "#0d366b"]
SEQ = LinearSegmentedColormap.from_list("seq", [SURFACE] + BLUE)
DIV = LinearSegmentedColormap.from_list("div", ["#b8322f", "#e34948", "#f3b3b2", "#f0efec",
                                                "#9ec5f4", "#3987e5", "#184f95"])
ORDINAL = ["#184f95", "#3987e5", "#86b6ef"]     # validated: ordinal, light surface

plt.rcParams.update({
    "font.family": "sans-serif", "font.size": 10, "text.color": INK, "axes.labelcolor": INK2,
    "xtick.color": INK2, "ytick.color": INK2, "axes.edgecolor": GRID, "figure.facecolor": SURFACE,
    "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE, "axes.spines.top": False,
    "axes.spines.right": False, "axes.titleweight": "bold", "axes.titlesize": 12,
    "axes.titlelocation": "left",
})


def cell_text(ax, M, fmt, cmap_max, threshold=0.55):
    for (i, j), v in np.ndenumerate(M):
        ax.text(j, i, fmt(v), ha="center", va="center", fontsize=8,
                color="#ffffff" if abs(v) / cmap_max > threshold else INK)


def theme_heatmap(res, check):
    themes, eras = res["themes"], res["eras"]
    M = np.array([[res["by_era"][e].get(t, 0) * 100 for e in eras] for t in themes])
    n = [res["by_era"][e]["_n"] for e in eras]
    fig, ax = plt.subplots(figsize=(8.6, 6.4))
    ax.imshow(M, cmap=SEQ, vmin=0, vmax=M.max(), aspect="auto")
    cell_text(ax, M, lambda v: f"{v:.0f}%", M.max())
    ax.set_xticks(range(len(eras)), [f"{e}\n{k} passages" for e, k in zip(eras, n)], fontsize=9)
    labels = []
    for t in themes:
        ok = check.get(t)
        labels.append(f"{t}  ({sum(ok)}/{len(ok)})" if ok else t)
    ax.set_yticks(range(len(themes)), labels)
    for tick, t in zip(ax.get_yticklabels(), themes):
        if t in check and sum(check[t]) <= 3:
            tick.set_color(MUTED)
    ax.tick_params(length=0)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.set_title("Share of each plan era's passages by theme")
    fig.text(0.01, 0.01, "In brackets: passages read and judged correctly assigned, of 5. Grey labels "
             "(3 of 5 or fewer) are not reliable enough to interpret.\n1948 is one report of 25 passages.",
             fontsize=8, color=INK2)
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    fig.savefig(DOCS / "theme_share_by_era.png", dpi=160)
    plt.close(fig)


def similarity(res):
    names = [res["short"][r] for r in res["reports"]]
    S = np.array(res["similarity"])
    np.fill_diagonal(S, np.nan)
    fig, ax = plt.subplots(figsize=(9.4, 8.2))
    lim = np.nanmax(np.abs(S))
    im = ax.imshow(S, cmap=DIV, norm=TwoSlopeNorm(0, -lim, lim))
    for (i, j), v in np.ndenumerate(S):
        if not np.isnan(v):
            ax.text(j, i, f"{v:.2f}".replace("0.", ".").replace("-.", "−."), ha="center", va="center",
                    fontsize=6.5, color="#ffffff" if abs(v) > 0.6 * lim else INK)
    ax.set_xticks(range(len(names)), names, rotation=90, fontsize=8)
    ax.set_yticks(range(len(names)), names, fontsize=8)
    ax.tick_params(length=0)
    for s in ax.spines.values():
        s.set_visible(False)
    cb = fig.colorbar(im, ax=ax, fraction=0.035, pad=0.02)
    cb.outline.set_visible(False)
    cb.set_label("Cosine similarity of plan centroids (centred)", color=INK2)
    ax.set_title("How alike the plans are in content")
    fig.tight_layout()
    fig.savefig(DOCS / "plan_similarity.png", dpi=160)
    plt.close(fig)


def carried(res):
    rows = res["carry"]
    names = [r["plan"] for r in rows][::-1]
    parts = [("repeated", "Repeated (similarity 0.95 or more)"), ("close", "Close precedent (0.80 to 0.95)"),
             ("new", "No close precedent (below 0.80)")]
    fig, ax = plt.subplots(figsize=(8.6, 6.2))
    left = np.zeros(len(rows))
    for (key, label), colour in zip(parts, ORDINAL):
        vals = np.array([r[key] for r in rows][::-1]) * 100
        ax.barh(names, vals, left=left, color=colour, edgecolor=SURFACE, linewidth=2, label=label, height=0.72)
        for y, (l, v) in enumerate(zip(left, vals)):
            if v >= 9:
                ax.text(l + v / 2, y, f"{v:.0f}%", ha="center", va="center", fontsize=8,
                        color="#ffffff" if colour != ORDINAL[2] else INK)
        left += vals
    ax.set_xlim(0, 100)
    ax.set_xlabel("Share of the plan's passages, by similarity to the closest passage in any earlier plan")
    ax.xaxis.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.tick_params(length=0)
    ax.spines["left"].set_visible(False)
    ax.legend(loc="upper center", bbox_to_anchor=(0.45, -0.1), ncol=3, frameon=False, fontsize=8)
    ax.set_title("How much of each plan restates an earlier one")
    fig.tight_layout()
    fig.savefig(DOCS / "carried_over_text.png", dpi=160)
    plt.close(fig)


def era_map(res, meta):
    xy = np.array(res["tsne"])
    eras = res["eras"]
    era_of = np.array([m["era"] for m in meta])
    fig, axes = plt.subplots(2, 3, figsize=(10.5, 7.2), sharex=True, sharey=True)
    for ax, e in zip(axes.flat, eras):
        on = era_of == e
        ax.scatter(xy[~on, 0], xy[~on, 1], s=5, color="#d9d8d3", linewidths=0)
        ax.scatter(xy[on, 0], xy[on, 1], s=9, color="#2a78d6", linewidths=0.4, edgecolors=SURFACE)
        ax.set_title(f"{e} ({on.sum()} passages)", fontsize=10)
        ax.set_xticks([]), ax.set_yticks([])
        for s in ax.spines.values():
            s.set_visible(False)
    fig.suptitle("Where each era's passages sit on a map of the whole corpus (t-SNE of the embeddings)",
                 x=0.01, ha="left", fontweight="bold", fontsize=12)
    fig.text(0.01, 0.01, "Each dot is a passage; nearby dots are similar in meaning. Grey: the other eras. "
             "The axes have no units.", fontsize=8, color=INK2)
    fig.tight_layout(rect=(0, 0.03, 1, 0.96))
    fig.savefig(DOCS / "era_map.png", dpi=160)
    plt.close(fig)


def clusters(res, names):
    c = res["clusters"]
    eras = res["eras"]
    ids = list(range(c["k"]))
    M = np.array([[c["by_era"][e].get(str(k), 0) * 100 for e in eras] for k in ids])
    order = np.argsort([np.argmax(r) * 10 - r.max() / 100 for r in M])   # by the era each peaks in
    M = M[order]
    fig, ax = plt.subplots(figsize=(9.6, 6.4))
    ax.imshow(M, cmap=SEQ, vmin=0, vmax=M.max(), aspect="auto")
    cell_text(ax, M, lambda v: f"{v:.0f}%", M.max())
    ax.set_xticks(range(len(eras)), eras)
    ax.set_yticks(range(len(ids)), [f"{names[ids[k]]}" for k in order], fontsize=9)
    ax.tick_params(length=0)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.set_title("Clusters found without the theme list: share of each era's passages")
    fig.text(0.01, 0.01, "Cluster names are given by the author from each cluster's most distinctive words "
             "and its central passages (docs/semantic/clusters.csv).", fontsize=8, color=INK2)
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(DOCS / "clusters_by_era.png", dpi=160)
    plt.close(fig)


CLUSTER_NAMES = {   # read from clusters.csv: distinctive words and the three central passages
    0: "Penn Connects building projects",
    1: "Plan statements and meetings (mixed)",
    2: "Building sites, Walnut Street development",
    3: "Parking, garages and commuting",
    4: "Commercial survey of nearby streets",
    5: "East campus, river and rail links",
    6: "Campus character and land-use principles",
    7: "Paths, approaches and building edges",
    8: "Committees, agencies and partners",
    9: "Classroom and laboratory space use",
    10: "Athletics and recreation",
    11: "Trees, planting and landscape",
}


def main():
    res = json.loads((OUT / "results.json").read_text())
    meta = [json.loads(line) for line in open(OUT / "passages.jsonl")]
    from penn_ocr.config import ANNOTATION
    check = json.loads((ANNOTATION / "semantic_theme_check.json").read_text())["judgements"]
    theme_heatmap(res, check)
    similarity(res)
    carried(res)
    era_map(res, meta)
    clusters(res, CLUSTER_NAMES)
    print("figures ->", DOCS)


if __name__ == "__main__":
    main()
