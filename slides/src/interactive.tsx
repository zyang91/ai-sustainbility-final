import { Fragment, useEffect, useState } from "react";
import examples from "./data/ocr_examples.json";
import demo from "./data/demo.json";

// ---------------------------------------------------------------- OCR example viewer
type Ex = { id: string; label: string; doc: string; year: number; page: number; split: string; image: string; tokens: [string, string][] };

export function OcrExamples() {
  const list = examples as unknown as Ex[];
  const [i, setI] = useState(0);
  const [showRef, setShowRef] = useState(true);
  const ex = list[i];
  return (
    <div className="col" style={{ gap: 20 }}>
      <div className="chips">
        {list.map((e, j) => (
          <button key={e.id} className={`chip ${j === i ? "on" : ""}`} onClick={() => setI(j)}>{e.label}</button>
        ))}
        <span style={{ flex: 1 }} />
        <button className={`chip ${showRef ? "" : "on"}`} onClick={() => setShowRef(!showRef)}>
          {showRef ? "Show only what OCR kept" : "Show what a person typed"}
        </button>
      </div>
      <div className="row" style={{ gap: 40, alignItems: "flex-start" }}>
        <div style={{ width: 640, flexShrink: 0 }}>
          <img className="crop" src={ex.image} alt={`Scanned paragraph, ${ex.year}, page ${ex.page}`} />
          <p className="note mt-s">{ex.doc}, page {ex.page} · {ex.split} partition</p>
        </div>
        <div className={`diff grow ${showRef ? "" : "hide-ref"}`}>
          {ex.tokens.map(([op, t], k) => (
            <Fragment key={k}>
              {op === "=" ? t : op === "-" ? <del title="In the scan, not in the OCR">{t}</del> : <ins title="OCR output">{t}</ins>}{" "}
            </Fragment>
          ))}
          <div className="row small mt-m" style={{ gap: 24 }}>
            <span><del style={{ fontSize: 17 }}>struck</del> in the scan, missing or wrong in OCR</span>
            <span><ins style={{ fontSize: 15 }}>mono</ins> what OCR wrote instead</span>
          </div>
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------- typewriter: the human transcription
/** Types out what the person typed for one benchmark crop, beside the crop. */
export function TypedBeside({ index = 0 }: { index?: number }) {
  const ex = (examples as unknown as Ex[])[index];
  const text = ex.tokens.filter(([op]) => op !== "+").map(([, t]) => t).join(" ");
  const [n, setN] = useState(0);
  useEffect(() => {
    setN(0);
    const id = setInterval(() => setN((k) => (k >= text.length ? k : k + 2)), 22);
    return () => clearInterval(id);
  }, [text]);
  return (
    <div className="row" style={{ gap: 56, alignItems: "flex-start" }}>
      <div style={{ width: 660, flexShrink: 0 }}>
        <img className="crop" src={ex.image} alt={`Scanned paragraph, ${ex.year}, page ${ex.page}`} />
        <p className="note mt-s">{ex.year}, page {ex.page}: what the typist sees</p>
      </div>
      <div className="grow">
        <p className="typed">{text.slice(0, n)}<span className="caret" /></p>
        <p className="note mt-s">what the typist enters, line by line, with no OCR text shown</p>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------- recorded RAG runs
type Src = { n: number; short: string; year: number; status: string; kind: string; section: string; page_start: number; page_end: number; text: string };
type Run = { id: string; question: string; kind: string; check: string; note: string; steps: { query: string; compare?: boolean; year_from?: number; year_to?: number }[]; answer: string; cited: number[]; sources: Src[] };

const CHECK_LABEL: Record<string, [string, string]> = {
  ok: ["Matches its sources", "ok"], bad: ["Wrong", "bad"], partial: ["Partly supported", "mixed"],
};
const RUN_LABEL: Record<string, string> = {
  "parking-1961": "Parking figure, 1961", "cars-1977": "Parking lots, 1977", "river-2006": "River land, 2006",
  pedestrian: "When did pedestrian space begin?", "parking-change": "Parking, 1960s to 1970s", singapore: "Singapore (not in archive)",
};

export function DemoReplay() {
  const runs = (demo as unknown as { runs: Run[] }).runs;
  const [id, setId] = useState(runs[0].id);
  const [phase, setPhase] = useState(0);
  const run = runs.find((r) => r.id === id)!;
  const [src, setSrc] = useState<number>(run.cited[0] ?? 1);

  useEffect(() => {
    setPhase(0);
    setSrc(run.cited[0] ?? 1);
    const t1 = setTimeout(() => setPhase(1), 450);
    const t2 = setTimeout(() => setPhase(2), 1300);
    const t3 = setTimeout(() => setPhase(3), 2000);
    return () => [t1, t2, t3].forEach(clearTimeout);
  }, [id]);

  // citations as the model wrote them: [2], [14, 15], and also [8, p. 42] or [1, (7)]
  const parts = run.answer.split(/(\[\d+[^\]\n]{0,20}\])/g);
  const s = run.sources.find((x) => x.n === src);
  const [label, tone] = CHECK_LABEL[run.check] ?? [run.check, "mixed"];

  return (
    <div className="col" style={{ gap: 18, height: "100%" }}>
      <div className="chips">
        {runs.map((r) => (
          <button key={r.id} className={`chip ${r.id === id ? "on" : ""}`} onClick={() => setId(r.id)}>{RUN_LABEL[r.id] ?? r.kind}</button>
        ))}
      </div>
      <div className="row" style={{ gap: 40, flex: 1, minHeight: 0 }}>
        <div className="col" style={{ flex: 1.25, minWidth: 0 }}>
          <p className="demo-q">“{run.question}”</p>
          <div className={`reveal ${phase >= 1 ? "in" : ""} mt-m`}>
            {run.steps.length === 0 && <span className="demo-step">one search</span>}
            {run.steps.map((st, k) => (
              <span key={k} className="demo-step">
                search: {st.query.length > 60 ? st.query.slice(0, 58) + "…" : st.query}
                {st.year_from || st.year_to ? ` · ${st.year_from ?? ""}–${st.year_to ?? ""}` : ""}{st.compare ? " · every plan" : ""}
              </span>
            ))}
            <span className="demo-step">{run.sources.length} passages → llama3.1:8b</span>
          </div>
          <div className={`reveal ${phase >= 2 ? "in" : ""} answer mt-m`} style={{ overflow: "auto", maxHeight: 340, paddingRight: 8 }}>
            {parts.map((p, k) => {
              const m = p.match(/^\[(.*)\]$/);
              if (!m) return <Fragment key={k}>{p}</Fragment>;
              return <Fragment key={k}>{m[1].split(",").map((x) => x.trim()).map((x, j) =>
                /^\d+$/.test(x)
                  ? <button key={j} className={`cite ${+x === src ? "on" : ""}`} onClick={() => setSrc(+x)}>{x}</button>
                  : <span key={j} className="note"> {x}</span>,
              )}</Fragment>;
            })}
          </div>
          <div className={`reveal ${phase >= 3 ? "in" : ""} mt-m`}>
            <span className={`badge ${tone}`}>Human check: {label}</span>
            <p className="small" style={{ marginTop: 6 }}>{run.note}</p>
          </div>
        </div>
        <div className="col" style={{ flex: 1, minWidth: 0 }}>
          <div className="chips" style={{ gap: 6 }}>
            {run.sources.map((x) => (
              <button key={x.n} className={`cite ${x.n === src ? "on" : ""}`} style={{ padding: "4px 9px", opacity: run.cited.includes(x.n) ? 1 : 0.55 }}
                onClick={() => setSrc(x.n)} title={run.cited.includes(x.n) ? "cited" : "retrieved, not cited"}>{x.n}</button>
            ))}
          </div>
          {s && <div className="aside mt-m" style={{ flex: 1, overflow: "auto" }}>
            <p className="small"><b>[{s.n}] {s.year} {s.short}</b>, p. {s.page_start}{s.page_end !== s.page_start ? `–${s.page_end}` : ""} · {s.status}
              {s.kind === "table" ? " · table" : ""} · {run.cited.includes(s.n) ? "cited" : <span className="red">retrieved, not cited</span>}</p>
            {s.section && <p className="note" style={{ marginTop: 2 }}>{s.section}</p>}
            <p className="source mt-s">{s.text}</p>
          </div>}
        </div>
      </div>
    </div>
  );
}
