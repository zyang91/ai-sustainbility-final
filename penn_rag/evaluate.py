"""Retrieval and answer evaluation (Vision 2.4).

    python -m penn_rag.evaluate --runs 3

Questions and their source pages are in annotation/rag_questions.json. Two
things are measured.

Retrieval alone, no language model: is a gold page among the passages returned
for the question as written, with no year filter? (A comparison question uses
the per-plan search and counts the periods covered.)

End to end, each question asked `--runs` times through `agent.run`:
  found     a gold page is among the passages the model was given
  cited     a gold page is among the passages the answer cites
  facts     the answer contains every expected fact
  grounded  every figure in the answer occurs in a passage it was given
  declined  (questions the archive cannot answer) the answer says so

`grounded` is a literal check on numbers. It catches invented figures; it
does not show that a sentence is supported by the passage it cites.

Output: work/rag/eval_runs.jsonl (every answer) and annotation/rag_eval.csv.
"""
import argparse
import csv
import json
import re
import time

from penn_ocr.config import ANNOTATION

from . import agent, llm, passages, retrieve
from .config import LLM_MODEL, RAG, TOP_K

QUESTIONS = ANNOTATION / "rag_questions.json"
RUNS = RAG / "eval_runs.jsonl"
TABLE = ANNOTATION / "rag_eval.csv"
DECLINE = re.compile(r"\b(do(es)? not|don't|doesn't|no) (\w+ ){0,3}(cover|mention|say|address|contain|"
                     r"provide|answer|information|reference|discuss)", re.I)


def holds(h: dict, group: list) -> bool:
    return any(h["doc_id"] == d and h["page_start"] <= p <= h["page_end"] for d, p in group)


def covered(hits: list[dict], gold: list) -> float:
    """Share of the gold groups (periods) with at least one page among the hits."""
    return sum(any(holds(h, g) for h in hits) for g in gold) / len(gold) if gold else 0.0


def rank(hits: list[dict], gold: list) -> int | None:
    return next((i for i, h in enumerate(hits, 1) if any(holds(h, g) for g in gold)), None)


def figures(text: str) -> set[str]:
    """Numbers of two or more digits, without citation marks, thousands separators or list numbers."""
    text = re.sub(r"\[[^\]]*\]", " ", text)
    text = re.sub(r"(?m)^\s*\d+[.)]\s", " ", text)
    return {m.replace(",", "") for m in re.findall(r"(?<![\w.])\d[\d,]*\.?\d*", text)
            if len(re.sub(r"\D", "", m)) >= 2}


def ungrounded(answer: str, question: str, sources: list[dict]) -> list[str]:
    known = " ".join(s["text"] for s in sources).replace(",", "") + " " + question
    known += " " + " ".join(f"{s['year']} {s['page_start']} {s['page_end']}" for s in sources)
    known += " " + retrieve.plan_years()
    decades = {str(y) for y in range(1900, 2030, 10)}          # "the 1960s"
    return sorted(n for n in figures(answer) if n.rstrip(".") not in known and n not in decades)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", type=int, default=3)
    ap.add_argument("--resume", action="store_true", help="keep the runs already in the log")
    args = ap.parse_args()
    qs = json.loads(QUESTIONS.read_text())["questions"]
    by_id = {p["id"]: p for p in passages.load()}
    rows, done = [], {}
    if args.resume and RUNS.exists():                   # keep finished runs after an interruption
        with open(RUNS) as f:
            for rec in map(json.loads, f):
                done[(rec["id"], rec["run"])] = rec
    with open(RUNS, "a" if done else "w") as log:
        for q in qs:
            row = dict(id=q["id"], kind=q["kind"])
            if q["gold"]:                                   # retrieval alone
                if q["kind"] == "over_time":
                    span = agent.period(q["question"]) or (None, None)
                    hits = retrieve.search_by_report(q["question"], year_from=span[0], year_to=span[1])
                    row.update(retrieval_rank="", retrieval_cover=round(covered(hits, q["gold"]), 2))
                else:
                    hits = retrieve.search(q["question"], k=20)
                    r = rank(hits, q["gold"])
                    row.update(retrieval_rank=r or "", retrieval_cover=float(bool(r and r <= TOP_K)))
            tally = dict(found=0, cited=0, facts=0, grounded=0, declined=0)
            for n in range(args.runs):
                if (q["id"], n) in done:
                    for k in tally:
                        tally[k] += done[(q["id"], n)][k]
                    continue
                t0 = time.time()
                try:
                    out = agent.run(q["question"])
                except llm.LLMError:                    # one retry: the local server sometimes stalls
                    time.sleep(5)
                    out = agent.run(q["question"])
                src = [dict(by_id[s["id"]], n=i) for i, s in enumerate(out["sources"], 1)]
                cited = [s for s in src if s["n"] in out["cited"]]
                bad = ungrounded(out["answer"], q["question"], src)
                res = dict(found=bool(q["gold"]) and covered(src, q["gold"]) == 1,
                           cited=bool(q["gold"]) and covered(cited, q["gold"]) == 1,
                           facts=bool(q["facts"]) and all(re.search(f, out["answer"], re.I) for f in q["facts"]),
                           grounded=not bad, declined=bool(DECLINE.search(out["answer"])))
                for k, v in res.items():
                    tally[k] += v
                log.write(json.dumps(dict(id=q["id"], run=n, seconds=round(time.time() - t0, 1),
                                          answer=out["answer"], cited_numbers=out["cited"], steps=out["steps"],
                                          sources=[f"{s['doc_id']} p{s['page_start']}-{s['page_end']}" for s in src],
                                          ungrounded=bad, **res), ensure_ascii=False) + "\n")
                log.flush()
            row.update(runs=args.runs, **tally)
            rows.append(row)
            print(row, flush=True)
    with open(TABLE, "w", newline="") as f:
        w = csv.DictWriter(f, ["id", "kind", "retrieval_rank", "retrieval_cover", "runs",
                               "found", "cited", "facts", "grounded", "declined"], restval="")
        w.writeheader()
        w.writerows(rows)
    print(f"model {LLM_MODEL}; {len(rows)} questions x {args.runs} runs -> {TABLE}")


if __name__ == "__main__":
    main()
