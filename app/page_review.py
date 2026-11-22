"""Page review for the full-corpus OCR.

    streamlit run app/page_review.py

Shows one scanned page at a time next to what the OCR read on it. The queue
holds only the pages worth a look: text the corpus left out because the
layout model called the area a figure, pages with little or no text, and
pages with low recognition confidence. One click per page; decisions go to
`annotation/page_checks.jsonl` and `python -m penn_ocr.corpus` applies them.
"""
import json
import sys
from pathlib import Path

import pymupdf
import streamlit as st
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from penn_ocr import documents, engines, pagecheck  # noqa: E402
from penn_ocr.config import DATA, PAGE_OCR  # noqa: E402

VIEW_DPI = 110
KEPT, LEFT_OUT = (30, 140, 60), (210, 50, 40)

st.set_page_config(page_title="Penn plan page review", layout="wide")
st.markdown("""<style>
.block-container {padding-top: 2.2rem; max-width: 1500px;}
.ocr {font-family: ui-monospace, Menlo, monospace; font-size: 13px; line-height: 1.45;
      white-space: pre-wrap; max-height: 62vh; overflow-y: auto; padding: 8px 10px;
      border: 1px solid rgba(128,128,128,.35); border-radius: 6px;}
.kept {border-left: 4px solid rgb(30,140,60);} .out {border-left: 4px solid rgb(210,50,40);}
</style>""", unsafe_allow_html=True)

docs = {d["doc_id"]: d for d in documents.load() if d["source"] == "scan"}


@st.cache_data(show_spinner=False)
def queue() -> list[dict]:
    return pagecheck.candidates(list(docs.values()))


@st.cache_data(show_spinner=False, max_entries=40)
def page_image(doc_id: str, page_no: int, boxes: bool) -> Image.Image:
    """The page as OCR saw it (upright), with the detected lines outlined."""
    page = json.loads((PAGE_OCR / doc_id / f"p{page_no:04d}.json").read_text())
    with pymupdf.open(DATA / docs[doc_id]["path"]) as pdf:
        pm = pdf[page_no - 1].get_pixmap(dpi=VIEW_DPI, colorspace=pymupdf.csRGB)
    img = Image.frombytes("RGB", (pm.width, pm.height), pm.samples)
    if page["rotation"]:
        img = img.rotate(page["rotation"], expand=True)
    if boxes:
        sx, sy = img.width / page["width"], img.height / page["height"]
        draw = ImageDraw.Draw(img)
        kept, left_out = pagecheck.split(page)
        for lines, colour in ((kept, KEPT), (left_out, LEFT_OUT)):
            for ln in lines:
                x0, y0, x1, y1 = ln["box"]
                draw.rectangle([x0 * sx, y0 * sy, x1 * sx, y1 * sy], outline=colour, width=2)
    return img


def as_text(lines: list[dict]) -> str:
    return "\n".join(" ".join(l["text"] for l in row) for row in engines.reading_order(lines))


def box(title: str, lines: list[dict], css: str):
    import html
    n = sum(len(l["text"]) for l in lines)
    st.markdown(f"**{title}** · {n:,} characters")
    st.markdown(f"<div class='ocr {css}'>{html.escape(as_text(lines)) or '<i>nothing</i>'}</div>",
                unsafe_allow_html=True)


items, done = queue(), pagecheck.latest()

# ---------------------------------------------------------------- sidebar
with st.sidebar:
    st.header("Page review")
    annotator = st.text_input("Annotator", key="annotator", placeholder="your initials")
    mode = st.radio("Show", ["Pages to review", "Pages already reviewed"])
    reasons = [r for r in pagecheck.REASONS if st.checkbox(
        f"{pagecheck.REASONS[r]} ({sum(i['reason'] == r for i in items)})",
        value=r != "empty", key=f"reason-{r}")]
    doc_filter = st.selectbox("Document", ["All documents"] + sorted({i["doc_id"] for i in items}))
    show_boxes = st.checkbox("Outline the detected lines", value=True)
    n_done = sum((i["doc_id"], i["page"]) in done for i in items)
    st.progress(n_done / len(items) if items else 1.0, text=f"{n_done} of {len(items)} pages reviewed")
    for r, label in pagecheck.REASONS.items():
        sub = [i for i in items if i["reason"] == r]
        st.caption(f"{label}: {sum((i['doc_id'], i['page']) in done for i in sub)} of {len(sub)}")
    with st.expander("What the buttons do", expanded=n_done == 0):
        st.markdown("""
Green outline = text that is in the corpus now. Red outline = text the OCR
read but the corpus left out.

- **Keep everything.** The red text is real content too. Put it in.
- **Keep green only.** Nothing changes. Use it when the red text is map
  labels or drawing annotations and the green text is fine.
- **Delete all text from this page.** Even the green text is junk
  (scribbles, stray marks, map labels).
- **Printed text has no box.** You can see printed paragraphs on the page
  with no outline at all: the OCR never read them. The page is listed for a
  second attempt.

Tick *Handwriting mixed in* when handwritten notes got into the text of a
page you are keeping.
""")

view = [i for i in items if i["reason"] in reasons
        and (doc_filter == "All documents" or i["doc_id"] == doc_filter)]
if mode == "Pages to review":
    skipped = st.session_state.setdefault("skipped", set())
    view = [i for i in view if (i["doc_id"], i["page"]) not in done
            and (i["doc_id"], i["page"]) not in skipped]
else:
    view = [i for i in view if (i["doc_id"], i["page"]) in done]

if not view:
    if mode == "Pages to review":
        st.success("Nothing left in this selection. Tick another reason in the sidebar, or run "
                   "`python -m penn_ocr.corpus` to apply your decisions.")
        if st.session_state.get("skipped") and st.button("Show the pages I skipped"):
            st.session_state["skipped"] = set()
            st.rerun()
    else:
        st.info("No reviewed pages in this selection yet.")
    st.stop()

if mode == "Pages already reviewed":
    pick = st.selectbox("Page", range(len(view)), format_func=lambda k: (
        f"{view[k]['doc_id']} p{view[k]['page']} · "
        f"{pagecheck.VERDICTS[done[(view[k]['doc_id'], view[k]['page'])]['verdict']]}"))
    item = view[pick]
else:
    item = view[0]

doc, key = docs[item["doc_id"]], (item["doc_id"], item["page"])
page = json.loads((PAGE_OCR / item["doc_id"] / f"p{item['page']:04d}.json").read_text())
kept, left_out = pagecheck.split(page)

st.caption(f"**{doc['title']}** ({doc['year']}, {doc['status']}) · page {item['page']} · "
           f"{len(view)} in this selection")
st.markdown(f"##### {pagecheck.REASONS[item['reason']]}")
if key in done:
    st.info(f"Current decision: {pagecheck.VERDICTS[done[key]['verdict']]}"
            + (f" · note: {done[key]['note']}" if done[key]["note"] else ""))

left, right = st.columns([11, 9])
with left:
    st.image(page_image(item["doc_id"], item["page"], show_boxes), use_container_width=True)
with right:
    note = st.text_input("Note (optional)", key=f"note-{key}")
    handwriting = st.checkbox("Handwriting mixed in with the kept text", key=f"hw-{key}")

    def decide(verdict: str):
        pagecheck.record(item["doc_id"], item["page"], verdict, item["reason"], note, annotator, handwriting)
        st.rerun()

    suggested = "keep" if item["reason"] == "dropped" else "figure"
    for v, label in pagecheck.VERDICTS.items():
        if st.button(label, key=f"{v}-{key}", use_container_width=True,
                     type="primary" if v == suggested else "secondary"):
            decide(v)
    c1, c2 = st.columns(2)
    if mode == "Pages to review":
        if c1.button("Skip for now", key=f"skip-{key}", use_container_width=True):
            st.session_state["skipped"].add(key)
            st.rerun()
    elif c1.button("Put back in the queue", key=f"reopen-{key}", use_container_width=True):
        decide("")
    box("Left out of the corpus (red)", left_out, "out")
    box("Kept in the corpus (green)", kept, "kept")
