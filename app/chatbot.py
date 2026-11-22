"""Historical plan chatbot (Vision Part 2).

    streamlit run app/chatbot.py

Ask a question in plain words. The assistant searches the plan corpus, answers
from the passages it found, and cites them by number. Every source can be
opened to read the passage and to see the scanned page it came from.

Without Ollama the app still searches and shows the passages; it just does
not write an answer.
"""
import io
import json
import re
import sys
from pathlib import Path

import pymupdf
import streamlit as st
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from penn_ocr import documents  # noqa: E402
from penn_ocr.config import DATA, PAGE_OCR  # noqa: E402
from penn_rag import agent, answer, llm, retrieve  # noqa: E402
from penn_rag.config import DB_DIR, EMBED_MODEL, LLM_MODEL  # noqa: E402

MODES = {
    "Agent": "The model plans its own searches and can search several times.",
    "Search once": "One search over the whole range, then an answer.",
    "Compare plans": "The best passages from every plan in the range, in date order.",
}
EXAMPLES = [
    "How did Penn's parking policies evolve between the 1950s and 1970s?",
    "What were the primary objectives of the 1960s campus development plans?",
    "When did Penn begin emphasizing pedestrian environments and open space?",
    "How did the plans describe Penn's relationship with West Philadelphia?",
]

st.set_page_config(page_title="Penn campus plans", layout="wide")
st.markdown("<style>.block-container {max-width: 1000px; padding-top: 2.2rem;}</style>",
            unsafe_allow_html=True)

if not DB_DIR.exists():
    st.error("No index yet. Run `python -m penn_rag.passages` and then `python -m penn_rag.index`.")
    st.stop()

docs = {d["doc_id"]: d for d in documents.load()}
years = sorted({d["year"] for d in docs.values() if not d["duplicate_of"]})


@st.cache_resource(show_spinner="Loading the search index...")
def warm():
    retrieve.search("campus plan", k=1)
    return True


@st.cache_data(show_spinner=False, max_entries=30)
def page_png(doc_id: str, page_no: int) -> bytes:
    with pymupdf.open(DATA / docs[doc_id]["path"]) as pdf:
        pm = pdf[page_no - 1].get_pixmap(dpi=110, colorspace=pymupdf.csRGB)
    img = Image.frombytes("RGB", (pm.width, pm.height), pm.samples)
    ocr = PAGE_OCR / doc_id / f"p{page_no:04d}.json"        # scans: turn the page upright
    if ocr.exists() and (angle := json.loads(ocr.read_text())["rotation"]):
        img = img.rotate(angle, expand=True)
    buf = io.BytesIO()
    img.save(buf, "PNG")
    return buf.getvalue()


def show_sources(sources: list[dict], cited: list[int], key: str):
    if not sources:
        return
    used = [i for i in range(1, len(sources) + 1) if i in cited]
    rest = [i for i in range(1, len(sources) + 1) if i not in cited]
    label = f"Sources: {len(used)} cited, {len(rest)} retrieved but not cited" if cited \
        else f"Retrieved passages: {len(sources)}"
    with st.expander(label, expanded=not cited):
        for i in used + rest:
            h = sources[i - 1]
            st.markdown(f"**[{i}]** {retrieve.cite(h)}"
                        + (f" · *{h['section']}*" if h["section"] else "")
                        + ("" if i in cited or not cited else " · not cited"))
            st.caption(h["text"])
            if st.toggle(f"Show page {h['page_start']} of the original", key=f"pg-{key}-{i}"):
                st.image(page_png(h["doc_id"], h["page_start"]), use_container_width=True)


warm()
problem = llm.status()

# ---------------------------------------------------------------- sidebar
with st.sidebar:
    st.header("Penn campus plans")
    st.caption(f"{len(years)} plan years, {years[0]} to {years[-1]}. Answers come only from the "
               "plans' own text and cite document and page.")
    mode = st.radio("How to search", list(MODES), captions=list(MODES.values()))
    y0, y1 = st.select_slider("Plan years", options=years, value=(years[0], years[-1]))
    status = st.radio("Documents", ["All", "Published plans only", "Drafts only"])
    if problem:
        st.warning(f"{problem}\n\nUntil then the app shows the passages it finds, without a written answer.")
    else:
        st.caption(f"Model: `{LLM_MODEL}` in Ollama · search: `{EMBED_MODEL}`")
    if st.button("Clear the conversation", use_container_width=True):
        st.session_state["turns"] = []
        st.rerun()

filters = dict(year_from=None if y0 == years[0] else y0, year_to=None if y1 == years[-1] else y1,
               status={"Published plans only": "final", "Drafts only": "draft"}.get(status))
turns = st.session_state.setdefault("turns", [])

if not turns:
    st.markdown("#### Ask about Penn's campus plans, 1948 to 2018")
    cols = st.columns(2)
    for i, q in enumerate(EXAMPLES):
        if cols[i % 2].button(q, key=f"ex-{i}", use_container_width=True):
            st.session_state["pending"] = q
            st.rerun()

for n, t in enumerate(turns):
    with st.chat_message("user"):
        st.markdown(t["question"])
    with st.chat_message("assistant"):
        for s in t.get("steps", []):
            st.caption("Searched: " + s["query"]
                       + (f" · {s.get('year_from', '')}-{s.get('year_to', '')}"
                          if s.get("year_from") or s.get("year_to") else "")
                       + (" · every plan" if s.get("compare") else ""))
        st.markdown(t["answer"])
        if t["sources"] and not t["cited"] and t.get("steps") is not None and not t["answer"].startswith("*No language"):
            st.warning("This answer cites none of the passages it was given. "
                       "Check it against the retrieved passages below before using it.")
        show_sources(t["sources"], t["cited"], str(n))

question = st.chat_input("Ask a question about the plans") or st.session_state.pop("pending", None)
if question:
    with st.chat_message("user"):
        st.markdown(question)
    with st.chat_message("assistant"):
        try:
            if problem:
                hits = retrieve.search_by_report(question, **filters) if mode == "Compare plans" \
                    else retrieve.search(question, **filters)
                out = dict(answer="*No language model is available, so here are the passages the "
                                  "search found.*", sources=hits, cited=[], steps=[])
            elif mode == "Agent":
                history = [m for t in turns[-3:] for m in (
                    {"role": "user", "content": t["question"]},
                    {"role": "assistant", "content": re.sub(r"\[[\d,\s]+\]", "", t["answer"])})]
                with st.status("Searching the plans...") as box:
                    out = agent.run(question, history, **filters,
                                    on_step=lambda s: box.write(f"Searching: {s['query']}"))
                    box.update(label=f"{len(out['steps'])} searches", state="complete")
            else:
                with st.spinner("Searching and writing..."):
                    out = answer.answer(question, by_report=mode == "Compare plans", **filters)
                    out["steps"] = []
        except llm.LLMError as e:
            st.error(str(e))
            st.stop()
        turns.append(dict(question=question, **out))
        st.rerun()
