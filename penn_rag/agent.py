"""Retrieval as a tool: the model decides what to search for, in which years,
and whether to search again before it answers. Questions about change over
time are routed in code to one search across every plan in the period.

    python -m penn_rag.agent "How did parking policy change between the 1960s and the 1980s?"

Passages keep one running number across all searches of a question, so a
citation [7] always points to the same passage.
"""
import json
import re
import sys

from . import llm, retrieve
from .answer import answer, cited

MAX_STEPS = 6

SYSTEM = """You are a research assistant for the University of Pennsylvania's historical campus plans.
The archive holds plans from these years only: {years}. There is no plan for any other year.
You have no knowledge of these plans except what the search_plans tool returns. Always search before answering.

How to work:
- Search with specific terms. If the result does not answer the question, search again with other words.
- Leave year_from and year_to empty unless the question names a period.
- For a question about change over time, set compare to true, or search each period separately.

How to answer:
- After every claim, cite the passage number in square brackets, like this: "The plan calls for 110 more acres [3]." Never cite by page or year alone. Cite only numbers the tool returned.
- Give the year of the plan each statement comes from. Do not describe a decade for which no passage was returned.
- Quote figures exactly as written. The text is OCR, so small typos are normal.
- A passage marked "table" is a table read row by row: column headings first, then one row per line. Name the row label and the column heading a figure comes from.
- Separate what a plan states from what you infer by comparing plans. Mark inference with "This suggests".
- Say that the plans mention something only if a passage contains it. If the searches do not answer the question, say "The plans I searched do not cover this." and say briefly what they do cover. Never use outside knowledge."""

TOOLS = [{"type": "function", "function": {
    "name": "search_plans",
    "description": "Search the text of Penn's campus plans. Returns numbered passages with document, year and page.",
    "parameters": {"type": "object", "properties": {
        "query": {"type": "string", "description": "What to look for, in plain words"},
        "year_from": {"type": "integer", "description": "Earliest plan year, only if the question names a period"},
        "year_to": {"type": "integer", "description": "Latest plan year, only if the question names a period"},
        "compare": {"type": "boolean",
                    "description": "true = the best passages from each plan in the range, for questions about change over time"},
    }, "required": ["query"]}}}]
RETRY = ("Your answer has no citations. Write it again with the passage number in square brackets "
         "after every sentence, like [3]. The valid numbers are 1 to {n}. Keep the content the same.")


OVER_TIME = re.compile(r"\b(when did|begin|began|first|earliest|evolv\w*|chang\w*|over time|shift\w*|"
                       r"histor\w*|trend\w*|compare\w*|differ\w*)\b", re.I)


def period(question: str) -> tuple[int, int] | None:
    """The span of years a question names: "1950s and 1970s" -> (1950, 1979).

    An 8B model often searches only the last decade mentioned, so the span is
    worked out here and handed to it as a hint.
    """
    spans = [(int(d), int(d) + 9) for d in re.findall(r"\b((?:19|20)\d0)s\b", question)]
    spans += [(int(y), int(y)) for y in re.findall(r"\b((?:19|20)\d\d)\b(?!s)", question)]
    return (min(a for a, _ in spans), max(b for _, b in spans)) if spans else None


def over_time(question: str) -> tuple[int | None, int | None] | None:
    """(year_from, year_to) when the question is about change over time, else None."""
    span = period(question)
    if span and span[1] - span[0] >= 5:
        return span
    return (None, None) if not span and OVER_TIME.search(question) else None


def _int(v):
    try:
        return int(v) if v not in (None, "", 0, "0") else None
    except (TypeError, ValueError):
        return None


def run(question: str, history: list[dict] | None = None, on_step=None,
        year_from: int | None = None, year_to: int | None = None, status: str | None = None) -> dict:
    """Answer one question. `history` is earlier user/assistant turns (text only).

    year_from / year_to / status come from the person, not the model: the
    model may narrow the years further but cannot widen them, and it cannot
    choose between drafts and published plans at all.
    """
    span = over_time(question)
    if span is not None:
        # Tested 2026-11-22 with llama3.1:8b: left to plan this itself, the model searched one
        # decade or lost its citations among 30 passages. One search over every plan in range,
        # answered in a single pass, was reliable, so the route is chosen here.
        filters = dict(year_from=max(filter(None, (span[0], year_from)), default=None),
                       year_to=min(filter(None, (span[1], year_to)), default=None), status=status)
        step = dict(query=question, compare=True, **{k: v for k, v in filters.items() if v})
        if on_step:
            on_step(step)
        out = answer(question, by_report=True, **filters)
        return dict(out, steps=[dict(step, n=len(out["sources"]))])
    messages = [{"role": "system", "content": SYSTEM.format(years=retrieve.plan_years())},
                *(history or []), {"role": "user", "content": question}]
    sources, steps = [], []
    for _ in range(MAX_STEPS):
        msg = llm.chat(messages, tools=TOOLS)
        messages.append(msg)
        calls = msg.get("tool_calls") or []
        if not calls:
            text = msg.get("content", "").strip()
            refs = cited(text, len(sources))
            declined = len(text) < 250 and re.search(r"\bdo(es)? not (cover|mention|say|address)", text)
            if sources and not refs and not declined:
                # Small models sometimes cite by page instead of by number. Ask once for a
                # rewrite, WITHOUT the tool: offered the tool, the model searched for the word
                # "citations" and then reported that the plans do not cover the question.
                again = llm.chat(messages + [{"role": "user", "content": RETRY.format(n=len(sources))}])
                rewritten = again.get("content", "").strip()
                if cited(rewritten, len(sources)):      # otherwise keep the first answer
                    text, refs = rewritten, cited(rewritten, len(sources))
            return dict(answer=text, sources=sources, cited=refs, steps=steps)
        for call in calls:
            args = call["function"].get("arguments") or {}
            if isinstance(args, str):
                args = json.loads(args or "{}")
            query = str(args.get("query", "")).strip() or question
            lo, hi = _int(args.get("year_from")), _int(args.get("year_to"))
            filters = dict(year_from=max(filter(None, (lo, year_from)), default=None),
                           year_to=min(filter(None, (hi, year_to)), default=None), status=status)
            compare = str(args.get("compare", "")).lower() in ("true", "1")
            hits = retrieve.search_by_report(query, **filters) if compare \
                else retrieve.search(query, **filters)
            lines = []
            for h in hits:
                known = next((i for i, s in enumerate(sources, 1) if s["id"] == h["id"]), None)
                if known is None:
                    sources.append(h)
                    known = len(sources)
                lines.append(f"[{known}] {retrieve.cite(h)}\n{h['text']}")
            gone = retrieve.missing_names(f"{question} . {query}", hits)
            if gone and hits:
                lines.append("Note: " + ", ".join(f'"{w}"' for w in gone)
                             + " does not appear in any of these passages.")
            step = dict(query=query, compare=compare, n=len(hits),
                        **{k: v for k, v in filters.items() if v})
            steps.append(step)
            if on_step:
                on_step(step)
            messages.append({"role": "tool", "tool_name": "search_plans",
                             "content": "\n\n".join(lines) or "No passages match. Try other words or a wider year range."})
    return dict(answer="Stopped after too many searches without an answer. Try a narrower question.",
                sources=sources, cited=[], steps=steps)


if __name__ == "__main__":
    q = " ".join(sys.argv[1:]) or "How did parking policy change between the 1960s and the 1980s?"
    out = run(q, on_step=lambda s: print("  search:", s))
    print("\n" + out["answer"] + "\n\nSources:")
    for i, h in enumerate(out["sources"], 1):
        print(f"  [{i}]{'*' if i in out['cited'] else ' '} {retrieve.cite(h)}")
