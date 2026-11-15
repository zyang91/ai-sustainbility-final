"""Mini Human Validator (Vision 1.3).

    streamlit run app/validator.py

Shows one cropped paragraph from a scanned page next to an empty box. The
annotator types exactly what the image shows. The transcribe and second-pass
modes never load OCR output, so the typing cannot be anchored to a model.

The last mode, "Check mismatched lines", is for after the blind passes: it
shows only the printed lines where the typed text differs from the second
typing or from the baseline OCR, and the annotator decides from the image.
"""
import difflib
import html
import random
import sys
import time
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from PIL import Image  # noqa: E402

from penn_ocr import linecheck, metrics, store  # noqa: E402
from penn_ocr.config import CROPS, SEED  # noqa: E402

RECHECK_SHARE = 0.15      # share of finished samples offered for a blind second pass
RECHECK_MIN = 5

st.set_page_config(page_title="Penn plan transcription", layout="wide")
st.markdown("""<style>
textarea {font-family: ui-monospace, Menlo, monospace !important; font-size: 15px !important;
          line-height: 1.5 !important;}
.block-container {padding-top: 2.2rem; max-width: 1100px;}
.diff {font-family: ui-monospace, Menlo, monospace; font-size: 14px; white-space: pre-wrap;}
.diff del {background: #f9c9c9; color: #111; text-decoration: none;} .diff ins {background: #bfe8c3; color: #111; text-decoration: none;}
</style>""", unsafe_allow_html=True)

samples = store.samples()
if not samples:
    st.error("No samples yet. Run `python -m penn_ocr.page_ocr` and then `python -m penn_ocr.regions`.")
    st.stop()
by_id = {s["sample_id"]: s for s in samples}
log = store.latest()


def recheck_ids() -> list[str]:
    """Seeded subset of finished samples to key a second time, blind."""
    done = [s["sample_id"] for s in samples
            if "first" in log.get(s["sample_id"], {})
            and "unusable" not in log[s["sample_id"]]["first"]["flags"]]
    k = min(len(done), max(RECHECK_MIN, round(RECHECK_SHARE * len(done))))
    picked = set(random.Random(SEED).sample(sorted(done), k)) if done else set()
    return [i for i in done if i in picked]


def diff_html(a: str, b: str) -> str:
    out = []
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if op in ("delete", "replace"):
            out.append(f"<del>{html.escape(a[i1:i2])}</del>")
        if op in ("insert", "replace"):
            out.append(f"<ins>{html.escape(b[j1:j2])}</ins>")
        if op == "equal":
            out.append(html.escape(a[i1:i2]))
    return f"<div class='diff'>{''.join(out)}</div>"


# ---------------------------------------------------------------- sidebar
with st.sidebar:
    st.header("Transcription")
    annotator = st.text_input("Annotator", key="annotator", placeholder="your initials")
    mode = st.radio("Mode", ["Transcribe", "Second pass (blind recheck)", "Review & reconcile",
                             "Check mismatched lines (shows OCR)"])
    n_first = sum("first" in log.get(s["sample_id"], {}) for s in samples)
    st.progress(n_first / len(samples), text=f"{n_first} of {len(samples)} regions transcribed")
    docs_done = len({s["doc_id"] for s in samples if "first" in log.get(s["sample_id"], {})})
    st.caption(f"Documents touched: {docs_done} of {len({s['doc_id'] for s in samples})}. "
               "The queue rotates through the documents, so you can stop at any point "
               "and still have a spread across the archive.")
    with st.expander("Transcription rules", expanded=n_first == 0):
        st.markdown("""
- Type **exactly** what is printed: spelling, capitals, punctuation, numbers, even typos.
- Press **Enter at the end of every printed line** so your lines match the image.
- Keep a hyphen at a line end as printed (`Develop-` then `ment` on the next line).
- Use plain keyboard quotes `"` `'` and `--` for long dashes.
- A character you cannot read: type `[?]` and tick *Unclear characters*.
- Skip handwriting, stamps and page numbers that are not part of the paragraph.
- Ignore a sliver of a neighbouring line cut off at the top or bottom edge.
- A crop that is a table, figure or mostly unreadable: tick *Not usable* and save.
""")

# ---------------------------------------------------------------- queue
if mode == "Transcribe":
    pass_ = "first"
    todo = [s["sample_id"] for s in samples if "first" not in log.get(s["sample_id"], {})]
elif mode.startswith("Second"):
    pass_ = "second"
    todo = [i for i in recheck_ids() if "second" not in log[i]]
elif mode.startswith("Check"):
    pass_ = "check"
    todo = []
else:
    pass_ = "final"
    todo = []


def transcribe(sample_id: str, pass_: str, prefill: str = "", flags=(), notes: str = ""):
    s = by_id[sample_id]
    if st.session_state.get("shown") != (sample_id, pass_):
        st.session_state["shown"] = (sample_id, pass_)
        st.session_state["t0"] = time.time()
    st.caption(f"**{s['title']}** ({s['year']}, {s['status']}) · page {s['page']} · `{sample_id}`")
    st.image(str(CROPS / f"{sample_id}.png"), use_container_width=True)
    text = st.text_area("Type exactly what the image shows, one printed line per line",
                        value=prefill, key=f"text-{pass_}-{sample_id}",
                        height=min(520, 90 + 26 * s["n_lines"]))
    typed = len(store.clean(text).split("\n")) if text.strip() else 0
    if typed and typed != s["n_lines"]:
        st.warning(f"You typed {typed} lines; the page detector counted {s['n_lines']} "
                   "printed lines. Check the line breaks (save anyway if the detector is wrong).")
    elif typed:
        st.caption(f"{typed} lines, matches the detected line count.")
    cols = st.columns(len(store.FLAGS))
    chosen = [k for col, (k, label) in zip(cols, store.FLAGS.items())
              if col.checkbox(label, value=k in flags, key=f"flag-{k}-{pass_}-{sample_id}")]
    note = st.text_input("Note (optional)", value=notes, key=f"note-{pass_}-{sample_id}")
    a, b = st.columns(2)
    if a.button("Save and next", type="primary", use_container_width=True):
        if not text.strip() and "unusable" not in chosen:
            st.error("Nothing typed. Type the text or tick *Not usable*.")
        else:
            store.save(sample_id, text, pass_, chosen, note, annotator,
                       time.time() - st.session_state["t0"])
            st.rerun()
    if b.button("Skip for now", use_container_width=True):
        st.session_state.setdefault("skipped", set()).add((sample_id, pass_))
        st.rerun()


if pass_ in ("first", "second"):
    skipped = st.session_state.get("skipped", set())
    queue = [i for i in todo if (i, pass_) not in skipped] or todo
    if not queue:
        if pass_ == "first":
            st.success("Every sampled region has a transcription. Run "
                       "`python -m penn_ocr.groundtruth` to build the benchmark table.")
        elif not recheck_ids():
            st.info("Transcribe some regions first; a subset will then be offered here "
                    "for an independent second pass.")
        else:
            st.success("Second pass complete. Open *Review & reconcile* to compare the two passes.")
        st.stop()
    st.subheader(f"{'Transcribe' if pass_ == 'first' else 'Second pass'} · {len(todo)} left")
    if pass_ == "second":
        st.caption("You typed this region before. Type it again from the image without looking "
                   "at your earlier text; disagreements reveal typing errors.")
    transcribe(queue[0], pass_)

# ---------------------------------------------------------------- line check
elif pass_ == "check":
    preds = linecheck.predictions()
    todo = linecheck.issues(samples, log, preds)
    st.subheader(f"Check mismatched lines · {len(todo)} left")
    if not preds:
        st.warning("No baseline OCR output found (`python -m penn_ocr.predict --engine paddle`); "
                   "only second-pass disagreements are listed.")
    if not todo:
        st.success("No open mismatches. Run `python -m penn_ocr.groundtruth` to rebuild the table.")
        st.stop()
    it = todo[0]
    sid, s = it["sample_id"], by_id[it["sample_id"]]
    ref = store.reference(log[sid])
    keys = [k for _, _, k in it["alts"]]
    st.caption(f"**{s['title']}** ({s['year']}) · page {s['page']} · `{sid}` · queue no. {s['order']}")

    def settle(decision: str, new_text: str):
        """Log the decision; store a new final text only if the text changed."""
        if store.clean(new_text) != ref["text"]:
            store.save(sid, new_text, "final", ref["flags"], ref["notes"], annotator)
        linecheck.record(sid, keys, decision, it["mine"],
                         new_text if it["kind"] != "line" else new_text.split("\n")[it["line"]],
                         annotator)
        st.rerun()

    crop = Image.open(CROPS / f"{sid}.png")
    if it["kind"] == "line":
        x0, y0, x1, y1 = store.sample_lines()[sid][it["line"]]
        st.image(crop.crop((0, max(0, int(y0) - 14), crop.width, min(crop.height, int(y1) + 14))),
                 use_container_width=True)
        st.markdown(f"Printed line {it['line'] + 1} of {s['n_lines']}. "
                    "Red = only in your text, green = only in the other reading.")
        lines = ref["text"].split("\n")

        def with_line(t: str) -> str:
            return "\n".join(lines[:it["line"]] + [t] + lines[it["line"] + 1:])

        for src, other, _ in it["alts"]:
            st.markdown(f"**{linecheck.SOURCES[src]}** says:")
            st.markdown(diff_html(it["mine"], other), unsafe_allow_html=True)
        edited = st.text_input("Correct text of this line", value=it["mine"], key="edit-" + keys[0])
        cols = st.columns(len(it["alts"]) + 1)
        if cols[0].button("Save the line as shown in the box", type="primary", use_container_width=True):
            settle("kept" if edited == it["mine"] else "edited", with_line(edited))
        for col, (src, other, _) in zip(cols[1:], it["alts"]):
            if col.button(f"{linecheck.SOURCES[src]} is right", use_container_width=True, key=f"use-{src}"):
                settle(f"took_{src}", with_line(other))
        with st.expander("Show the whole paragraph"):
            st.image(crop, use_container_width=True)
    else:
        st.image(crop, use_container_width=True)
        src, other, _ = it["alts"][0]
        if it["kind"] == "missing":
            st.markdown(f"**{linecheck.SOURCES[src]}** has a line that your text does not. "
                        "If you skipped it, add it below; if it is not part of the paragraph, save unchanged.")
            st.code(other, language=None)
        else:
            st.markdown("Your line breaks do not follow the print, so the whole paragraph is compared. "
                        f"Red = only in your text, green = only in **{linecheck.SOURCES[src]}**.")
            st.markdown(diff_html(metrics.normalize(it["mine"]), metrics.normalize(other)),
                        unsafe_allow_html=True)
        edited = st.text_area("Your text (one printed line per line)", value=ref["text"],
                              key="edit-" + keys[0], height=min(520, 90 + 26 * s["n_lines"]))
        if st.button("Save", type="primary", use_container_width=True):
            settle("kept" if store.clean(edited) == ref["text"] else "edited", edited)

# ---------------------------------------------------------------- review
else:
    st.subheader("Review & reconcile")
    rows = []
    for s in samples:
        passes = log.get(s["sample_id"], {})
        if "first" not in passes:
            continue
        ref = store.reference(passes)
        c = metrics.cer(passes["first"]["text"], passes["second"]["text"]) \
            if "second" in passes and passes["first"]["text"] else None
        rows.append(dict(sample_id=s["sample_id"], year=s["year"], page=s["page"],
                         lines_typed=ref["text"].count("\n") + 1 if ref["text"] else 0,
                         lines_detected=s["n_lines"], flags=", ".join(ref["flags"]),
                         second_pass_cer=c, reconciled="final" in passes, note=ref["notes"]))
    if not rows:
        st.info("Nothing transcribed yet.")
        st.stop()
    only = st.radio("Show", ["All", "Flagged", "Line-count mismatch", "Passes disagree"], horizontal=True)
    keep = {"All": lambda r: True, "Flagged": lambda r: bool(r["flags"]),
            "Line-count mismatch": lambda r: r["lines_typed"] != r["lines_detected"],
            "Passes disagree": lambda r: bool(r["second_pass_cer"]) and not r["reconciled"]}[only]
    rows = [r for r in rows if keep(r)]
    st.dataframe(rows, use_container_width=True, hide_index=True)
    if rows:
        sid = st.selectbox("Open a sample to correct it", [r["sample_id"] for r in rows])
        passes = log[sid]
        ref = store.reference(passes)
        if "second" in passes:
            st.markdown("**First pass vs second pass** (red = first only, green = second only)")
            st.markdown(diff_html(passes["first"]["text"], passes["second"]["text"]),
                        unsafe_allow_html=True)
        st.caption("Editing here saves a reconciled *final* text; both original passes stay in the log.")
        transcribe(sid, "final", prefill=ref["text"], flags=ref["flags"], notes=ref["notes"])
