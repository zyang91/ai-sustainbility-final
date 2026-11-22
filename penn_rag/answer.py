"""Search-and-answer: retrieve passages, then let the local model answer from
them with numbered citations.

    python -m penn_rag.answer "What were the objectives of the 1961 Development Plan?"
    python -m penn_rag.answer "How did parking policy change?" --by-report --from 1948 --to 1980

The model sees only the retrieved passages. Each is numbered; the answer must
cite those numbers, and the numbers map back to a document and page.
"""
import argparse
import re

from . import llm, retrieve

SYSTEM = """You are a research assistant for the University of Pennsylvania's historical campus plans.
Answer ONLY from the numbered passages below. They are OCR text from the original plans, so small typos are normal.

Rules:
- After every claim, cite the passage number in square brackets, like this: "The plan calls for 110 more acres [3]." Never cite by page or year alone. Cite only numbers that appear below.
- Say that the plans mention something only if a passage contains it.
- Give the year of the plan a statement comes from. Do not carry a statement from one plan over to another year.
- Quote figures (parking spaces, acres, dates, enrolment) exactly as written.
- A passage marked TABLE is a table read row by row: the first rows are column headings, then one row per line with its numbers in column order. Name the row label and the column heading a figure comes from.
- Separate what a plan states from what you infer by comparing plans. Mark inference with "This suggests".
- When passages come from several plans, go through them in date order, one plan at a time, and skip a plan whose passages are not about the question.
- The archive holds plans from these years only: {years}. Say so if the question asks about a year with no plan.
- If the passages do not answer the question, say "The retrieved passages do not answer this." and say what they do cover. Never use outside knowledge."""


def context(hits: list[dict]) -> str:
    return "\n\n".join(
        f"[{i}] {h['title']} ({h['year']}, {h['status']}), "
        f"{'p. ' + str(h['page_start']) if h['page_start'] == h['page_end'] else 'pp. %d-%d' % (h['page_start'], h['page_end'])}"
        + (f", TABLE \"{h['section']}\"" if h.get("kind") == "table"
           else f", section \"{h['section']}\"" if h["section"] else "") + f"\n{h['text']}"
        for i, h in enumerate(hits, 1))


def cited(text: str, n: int) -> list[int]:
    """Passage numbers the answer actually cites (valid ones only)."""
    # "[2]", "[2, 5]" and the looser "[8, p. 42]": the numbers that open the bracket
    nums = {int(x) for group in re.findall(r"\[\s*(\d+(?:\s*,\s*\d+)*)(?=[\],])", text)
            for x in re.findall(r"\d+", group)}
    return sorted(x for x in nums if 1 <= x <= n)


def note(question: str, hits: list[dict]) -> str:
    gone = retrieve.missing_names(question, hits)
    return "" if not gone else ("\n\nNote: " + ", ".join(f'"{w}"' for w in gone)
                                + " does not appear in any of these passages.")


def answer(question: str, by_report: bool = False, **filters) -> dict:
    hits = retrieve.search_by_report(question, **filters) if by_report \
        else retrieve.search(question, **filters)
    if not hits:
        return dict(answer="No passages match these filters.", sources=[], cited=[])
    reply = llm.chat([{"role": "system", "content": SYSTEM.format(years=retrieve.plan_years())},
                      {"role": "user", "content": f"{context(hits)}{note(question, hits)}\n\nQuestion: {question}"}])
    text = reply.get("content", "").strip()
    return dict(answer=text, sources=hits, cited=cited(text, len(hits)))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("question")
    ap.add_argument("--from", dest="year_from", type=int)
    ap.add_argument("--to", dest="year_to", type=int)
    ap.add_argument("--status", choices=["final", "draft"])
    ap.add_argument("--by-report", action="store_true")
    a = ap.parse_args()
    out = answer(a.question, a.by_report, year_from=a.year_from, year_to=a.year_to, status=a.status)
    print(out["answer"], "\n\nSources:")
    for i, h in enumerate(out["sources"], 1):
        print(f"  [{i}]{'*' if i in out['cited'] else ' '} {retrieve.cite(h)}")
