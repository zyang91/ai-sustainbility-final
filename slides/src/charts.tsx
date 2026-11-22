import { useMemo, useRef, useState, type ReactNode } from "react";
import documents from "./data/documents.json";
import themeByEra from "./data/theme_by_era.json";
import themeByPlan from "./data/theme_by_plan.json";
import themeCheck from "./data/theme_check.json";
import similarity from "./data/similarity.json";
import carried from "./data/carried.json";
import tsneData from "./data/tsne.json";
import ragEval from "./data/rag_eval.json";
import ragQuestions from "./data/rag_questions.json";

// ---------------------------------------------------------------- shared
const BLUES = ["#f3f1ea", "#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"];
function seq(t: number) {               // 0..1 -> sequential blue
  const x = Math.max(0, Math.min(1, t)) * (BLUES.length - 1);
  const i = Math.floor(x);
  return i >= BLUES.length - 1 ? BLUES[BLUES.length - 1] : mix(BLUES[i], BLUES[i + 1], x - i);
}
function mix(a: string, b: string, t: number) {
  const p = (h: string) => [1, 3, 5].map((i) => parseInt(h.slice(i, i + 2), 16));
  const [x, y] = [p(a), p(b)];
  return "#" + x.map((v, i) => Math.round(v + (y[i] - v) * t).toString(16).padStart(2, "0")).join("");
}
function diverging(v: number, lim: number) {  // red < 0 < blue, grey at zero
  const t = Math.max(-1, Math.min(1, v / lim));
  return t < 0 ? mix("#efede7", "#b8322f", -t) : mix("#efede7", "#184f95", t);
}
const pct = (v: number, d = 0) => `${(v * 100).toFixed(d)}%`;

/** Tooltip that follows the pointer inside a scaled stage. */
function useTip() {
  const box = useRef<HTMLDivElement>(null);
  const [tip, setTip] = useState<{ x: number; y: number; body: ReactNode } | null>(null);
  const show = (e: React.MouseEvent, body: ReactNode) => {
    const el = box.current!;
    const r = el.getBoundingClientRect();
    const k = el.offsetWidth / r.width;
    const x = (e.clientX - r.left) * k, y = (e.clientY - r.top) * k;
    setTip({ x: x > el.offsetWidth * 0.62 ? x - 440 : x + 18, y: y + 18, body });
  };
  const node = tip && <div className="tip" style={{ left: tip.x, top: tip.y }}>{tip.body}</div>;
  return { box, show, hide: () => setTip(null), node };
}

// ---------------------------------------------------------------- archive timeline
type Doc = { id: string; year: number; title: string; status: string; source: string; pages: number };
const DUPLICATES = new Set(["1961_dev_plan_taubin", "1963_dev_plan_taubin", "1966_campus_dev_plan_ua"]);

export function ArchiveTimeline() {
  const { box, show, hide, node } = useTip();
  const docs = (documents as Doc[]);
  const W = 1340, H = 330, x0 = 1944, x1 = 2021, base = 270;
  const x = (y: number) => 20 + ((y - x0) / (x1 - x0)) * (W - 40);
  const byYear = new Map<number, Doc[]>();
  docs.forEach((d) => byYear.set(d.year, [...(byYear.get(d.year) ?? []), d]));
  const k = 0.88;                                           // px per page
  return (
    <div ref={box} style={{ position: "relative" }} onMouseLeave={hide}>
      <svg width={W} height={H} role="img" aria-label="Documents in the archive by year and page count">
        {[[1949, 1960], [1967, 1976]].map(([a, b]) => (
          <g key={a}>
            <rect x={x(a - 0.5)} y={20} width={x(b + 0.5) - x(a - 0.5)} height={base - 20} fill="#ebe8df" />
            <text x={(x(a - 0.5) + x(b + 0.5)) / 2} y={base - 14} textAnchor="middle" fontSize={16} fill="#8a877e">no plans, {a}–{b}</text>
          </g>
        ))}
        {[...byYear.entries()].map(([year, ds]) => {
          let top = base;
          return ds.sort((a, b) => b.pages - a.pages).map((d) => {
            const h = Math.max(3, d.pages * k);
            top -= h + 2;
            const dup = DUPLICATES.has(d.id);
            const fill = dup ? "#d4d1c7" : d.source === "scan" ? "#1c5cab" : "#86b6ef";
            return (
              <rect key={d.id} className="cell" x={x(year) - 9} y={top} width={18} height={h} rx={2}
                fill={d.status === "draft" && !dup ? "url(#hatch)" : fill}
                stroke={d.status === "draft" && !dup ? fill : "none"} strokeWidth={1.5}
                onMouseMove={(e) => show(e, <><b>{d.year}</b> · {d.pages} pages · {d.status}{dup ? " · second scan, left out" : ""}<br />{d.title}</>)} />
            );
          });
        })}
        <defs>
          <pattern id="hatch" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
            <rect width="6" height="6" fill="#fdfcf9" /><line x1="0" y1="0" x2="0" y2="6" stroke="#1c5cab" strokeWidth="2.4" />
          </pattern>
        </defs>
        <line x1={0} x2={W} y1={base} y2={base} stroke="#8a877e" />
        <g className="axis">
          {[1948, 1961, 1966, 1977, 1982, 1987, 1992, 1998, 2006, 2012, 2018].map((y) => (
            <text key={y} x={x(y)} y={base + 26} textAnchor="middle">{y}</text>
          ))}
        </g>
      </svg>
      <div className="row small" style={{ gap: 28, marginTop: 6 }}>
        <Key swatch="#1c5cab">Scanned, published</Key>
        <Key swatch="url" >Scanned, draft</Key>
        <Key swatch="#86b6ef">Born-digital (text layer)</Key>
        <Key swatch="#d4d1c7">Second scan of a plan, left out</Key>
        <span className="note">Bar height = pages. Hover a bar for the document.</span>
      </div>
      {node}
    </div>
  );
}

function Key({ swatch, children }: { swatch: string; children: ReactNode }) {
  const style = swatch === "url"
    ? { background: "repeating-linear-gradient(45deg,#1c5cab 0 2px,#fdfcf9 2px 5px)", border: "1.5px solid #1c5cab" }
    : { background: swatch };
  return <span style={{ display: "inline-flex", alignItems: "center", gap: 8 }}>
    <i style={{ width: 14, height: 14, borderRadius: 2, display: "inline-block", ...style }} />{children}
  </span>;
}

// ---------------------------------------------------------------- CER bars
const CER = [
  { split: "Test (held out)", n: "33 paragraphs", pre: 0.63, ft: 0.62 },
  { split: "Validation", n: "20 paragraphs", pre: 1.24, ft: 1.21 },
  { split: "Train", n: "39 paragraphs", pre: 0.24, ft: 0.16 },
];
export function CerChart() {
  const { box, show, hide, node } = useTip();
  const W = 780, rowH = 104, x = (v: number) => 190 + (v / 1.4) * (W - 260);
  return (
    <div ref={box} style={{ position: "relative" }} onMouseLeave={hide}>
      <svg width={W} height={CER.length * rowH + 86}>
        <line x1={x(0.7)} x2={x(0.7)} y1={30} y2={CER.length * rowH + 14} stroke="#990000" strokeDasharray="5 4" strokeWidth={1.5} />
        <text x={x(0.7)} y={CER.length * rowH + 74} textAnchor="middle" fontSize={15} fill="#990000">0.7%: two people typing the same paragraph</text>
        {CER.map((r, i) => (
          <g key={r.split} transform={`translate(0, ${i * rowH + 34})`}>
            <text x={0} y={22} fontSize={19} fill="#15140f">{r.split}</text>
            <text x={0} y={46} fontSize={14} fill="#8a877e">{r.n}</text>
            {[["Pretrained", r.pre, "#86b6ef"], ["Fine-tuned", r.ft, "#1c5cab"]].map(([lab, v, c], j) => (
              <g key={lab as string} onMouseMove={(e) => show(e, <><b>{r.split}</b><br />{lab}: CER {String(v)}%</>)}>
                <rect x={x(0)} y={j * 30 + 4} width={x(v as number) - x(0)} height={24} rx={3} fill={c as string} />
                <text x={x(v as number) + 8} y={j * 30 + 22} fontSize={16} fill="#15140f" className="num">{(v as number).toFixed(2)}%</text>
              </g>
            ))}
          </g>
        ))}
        <g className="axis" transform={`translate(0, ${CER.length * rowH + 30})`}>
          {[0, 0.5, 1].map((v) => <text key={v} x={x(v)} textAnchor="middle">{v}%</text>)}
        </g>
      </svg>
      <div className="row small" style={{ gap: 24 }}><Key swatch="#86b6ef">Pretrained PP-OCRv6</Key><Key swatch="#1c5cab">Fine-tuned on 209 lines</Key></div>
      {node}
    </div>
  );
}

// ---------------------------------------------------------------- generic proportion bars
export function Bars({ rows, width = 700, max = 1 }: {
  rows: { label: string; value: number; text: string; tone?: "bad" | "muted" }[]; width?: number; max?: number;
}) {
  const lw = 330, bw = width - lw - 130;
  return (
    <svg width={width} height={rows.length * 52 + 4}>
      {rows.map((r, i) => (
        <g key={r.label} transform={`translate(0, ${i * 52})`}>
          <text x={0} y={27} fontSize={19} fill="#15140f">{r.label}</text>
          <rect x={lw} y={10} width={bw} height={24} rx={3} fill="#ebe8df" />
          <rect x={lw} y={10} width={Math.max(2, (r.value / max) * bw)} height={24} rx={3}
            fill={r.tone === "bad" ? "#b8322f" : r.tone === "muted" ? "#9ec5f4" : "#1c5cab"} />
          <text x={lw + bw + 12} y={28} fontSize={18} fill="#15140f" className="num">{r.text}</text>
        </g>
      ))}
    </svg>
  );
}

// ---------------------------------------------------------------- theme heatmap
type Row = Record<string, string | number>;
export const THEMES = Object.keys(themeByEra[0]).filter((k) => !["era", "passages", "Other"].includes(k));
const CHECK = themeCheck as Record<string, number>;

export function ThemeHeatmap() {
  const { box, show, hide, node } = useTip();
  const [sel, setSel] = useState<string>("Parking and traffic");
  const eras = (themeByEra as Row[]).map((r) => String(r.era));
  const max = Math.max(...(themeByEra as Row[]).flatMap((r) => THEMES.map((t) => Number(r[t]))));
  const cw = 104, ch = 38, lw = 300;
  const plans = themeByPlan as Row[];
  const pmax = Math.max(...plans.map((p) => Number(p[sel])));
  return (
    <div ref={box} className="row" style={{ position: "relative", gap: 40 }} onMouseLeave={hide}>
      <svg width={lw + eras.length * cw} height={THEMES.length * ch + 64}>
        {eras.map((e, j) => (
          <text key={e} x={lw + j * cw + cw / 2} y={20} textAnchor="middle" fontSize={16} fill="#4b4a44">{e}</text>
        ))}
        {THEMES.map((t, i) => {
          const ok = CHECK[t] ?? 0, weak = ok <= 3, on = t === sel;
          return (
            <g key={t} transform={`translate(0, ${36 + i * ch})`} style={{ cursor: "pointer" }} onClick={() => setSel(t)}>
              <rect x={0} y={0} width={lw - 12} height={ch - 4} fill={on ? "#e3e9f5" : "transparent"} rx={3} />
              <text x={10} y={ch / 2 + 4} fontSize={17} fill={weak ? "#a19e94" : "#15140f"} fontWeight={on ? 600 : 400}>{t}</text>
              <text x={lw - 22} y={ch / 2 + 4} fontSize={14} textAnchor="end" fill={weak ? "#a19e94" : "#4b4a44"}>{ok}/5</text>
              {eras.map((e, j) => {
                const v = Number((themeByEra as Row[])[j][t]);
                return (
                  <g key={e} onMouseMove={(ev) => show(ev, <><b>{t}</b> · {e}<br />{pct(v, 1)} of the period's passages</>)}>
                    <rect className="cell" x={lw + j * cw + 2} y={0} width={cw - 4} height={ch - 4} rx={2}
                      fill={seq(v / max)} opacity={weak ? 0.45 : 1} />
                    <text x={lw + j * cw + cw / 2} y={ch / 2 + 4} textAnchor="middle" fontSize={15} className="num"
                      fill={v / max > 0.55 ? "#fff" : "#15140f"} pointerEvents="none">{pct(v)}</text>
                  </g>
                );
              })}
            </g>
          );
        })}
      </svg>
      <div className="col grow" style={{ paddingTop: 4 }}>
        <h3 style={{ fontSize: 24 }}>{sel}, plan by plan</h3>
        <p className="note" style={{ marginTop: 4 }}>Click a theme on the left. Checked correct on {CHECK[sel]} of 5 passages read.</p>
        <svg width={380} height={plans.length * 26 + 10} style={{ marginTop: 12 }}>
          {plans.map((p, i) => {
            const v = Number(p[sel]);
            return (
              <g key={String(p.plan)} transform={`translate(0, ${i * 26})`}
                onMouseMove={(ev) => show(ev, <><b>{String(p.plan)}</b><br />{pct(v, 1)} of {String(p.passages)} passages</>)}>
                <text x={0} y={17} fontSize={14} fill="#4b4a44">{String(p.plan).replace(" (draft)", "*")}</text>
                <rect x={200} y={5} width={Math.max(1.5, (v / Math.max(pmax, 0.01)) * 140)} height={16} rx={2} fill="#1c5cab" />
                <text x={200 + (v / Math.max(pmax, 0.01)) * 140 + 6} y={18} fontSize={13} fill="#15140f" className="num">{pct(v)}</text>
              </g>
            );
          })}
        </svg>
        <p className="note">* draft</p>
      </div>
      {node}
    </div>
  );
}

// ---------------------------------------------------------------- two themes over time
export function TwoThemes({ W = 720, H = 400 }: { W?: number; H?: number } = {}) {
  const { box, show, hide, node } = useTip();
  const rows = themeByEra as Row[];
  const series = [
    { t: "Pedestrian circulation", c: "#1c5cab" },
    { t: "Parking and traffic", c: "#b07a1a" },
  ];
  const l = 60, r = 140, top = 20, bot = 50;
  const x = (j: number) => l + (j / (rows.length - 1)) * (W - l - r);
  const y = (v: number) => top + (1 - v / 0.14) * (H - top - bot);
  return (
    <div ref={box} style={{ position: "relative" }} onMouseLeave={hide}>
      <svg width={W} height={H}>
        <g className="axis">
          {[0, 0.05, 0.1].map((v) => (
            <g key={v}><line x1={l} x2={W - r} y1={y(v)} y2={y(v)} /><text x={l - 10} y={y(v) + 5} textAnchor="end">{v * 100}%</text></g>
          ))}
          {rows.map((rw, j) => <text key={j} x={x(j)} y={H - 18} textAnchor="middle">{String(rw.era)}</text>)}
        </g>
        {series.map((s) => {
          const pts = rows.map((rw, j) => [x(j), y(Number(rw[s.t]))] as const);
          const last = pts[pts.length - 1];
          return (
            <g key={s.t}>
              <polyline points={pts.map((p) => p.join(",")).join(" ")} fill="none" stroke={s.c} strokeWidth={2.5} />
              {pts.map(([px, py], j) => (
                <circle key={j} cx={px} cy={py} r={6} fill={s.c} stroke="#f6f4ee" strokeWidth={2}
                  onMouseMove={(e) => show(e, <><b>{s.t}</b> · {String(rows[j].era)}<br />{pct(Number(rows[j][s.t]), 1)} of {String(rows[j].passages)} passages</>)} />
              ))}
              <text x={last[0] + 14} y={last[1] + 5} fontSize={17} fill="#15140f">{s.t.split(" ")[0]}</text>
            </g>
          );
        })}
      </svg>
      {node}
    </div>
  );
}

// ---------------------------------------------------------------- similarity matrix
export function SimilarityMatrix() {
  const { box, show, hide, node } = useTip();
  const [focus, setFocus] = useState<number | null>(3);         // the 1966 plan: the clearest lineage
  const P = similarity.plans, M = similarity.matrix;
  const lim = Math.max(...M.flatMap((r, i) => r.filter((_, j) => j !== i).map(Math.abs)));
  const cs = 34, lw = 250;
  const near = focus === null ? [] : M[focus].map((v, j) => [v, j] as const).filter(([, j]) => j !== focus)
    .sort((a, b) => b[0] - a[0]).slice(0, 3);
  return (
    <div ref={box} className="row" style={{ position: "relative", gap: 36 }} onMouseLeave={hide}>
      <svg width={lw + P.length * cs + 4} height={P.length * cs + 4}>
        {P.map((p, i) => (
          <text key={p} x={lw - 10} y={i * cs + cs / 2 + 5} textAnchor="end" fontSize={14.5} style={{ cursor: "pointer" }}
            fill={i === focus ? "#011f5b" : "#4b4a44"} fontWeight={i === focus ? 600 : 400} onClick={() => setFocus(i)}>{p}</text>
        ))}
        {M.map((r, i) => r.map((v, j) => (
          <rect key={`${i}-${j}`} className="cell" x={lw + j * cs + 1} y={i * cs + 1} width={cs - 2} height={cs - 2}
            fill={i === j ? "#f6f4ee" : diverging(v, lim)}
            opacity={focus === null || i === focus || j === focus ? 1 : 0.35}
            onClick={() => setFocus(i)}
            onMouseMove={(e) => i !== j && show(e, <><b>{P[i]}</b><br />vs {P[j]}<br />similarity {v.toFixed(2)}</>)} />
        )))}
      </svg>
      <div className="col" style={{ width: 400 }}>
        {focus !== null && <>
          <p className="note">Selected (click any row)</p>
          <h3 style={{ fontSize: 26, marginTop: 4 }}>{P[focus]}</h3>
          <p className="small mt-s">Closest plans:</p>
          {near.map(([v, j]) => (
            <div key={j} className="row" style={{ gap: 12, alignItems: "baseline", marginTop: 8 }}>
              <span className="figure-mid" style={{ fontSize: 34, width: 80 }}>{v.toFixed(2)}</span>
              <span className="small">{P[j]}</span>
            </div>
          ))}
        </>}
        <div className="mt-l">
          <div style={{ height: 14, borderRadius: 2, background: `linear-gradient(90deg, #b8322f, #efede7, #184f95)` }} />
          <div className="row note" style={{ justifyContent: "space-between", gap: 0, marginTop: 4 }}>
            <span>less alike than average</span><span>0</span><span>more alike</span>
          </div>
          <p className="note mt-s">Cosine of plan centroids after the corpus mean is subtracted. Without that step every pair scores 0.90 to 0.99.</p>
        </div>
      </div>
      {node}
    </div>
  );
}

// ---------------------------------------------------------------- carried-over text
type Carry = { plan: string; passages: number; repeated: number; close: number; new: number; repeated_from: string };
export function CarriedBars() {
  const { box, show, hide, node } = useTip();
  const rows = (carried as Carry[]).slice(1);
  const lw = 250, bw = 560, rh = 30;
  const parts: [keyof Carry, string, string][] = [
    ["repeated", "Repeated (≥ 0.95)", "#184f95"], ["close", "Close precedent (0.80–0.95)", "#3987e5"], ["new", "No close precedent", "#cde2fb"],
  ];
  return (
    <div ref={box} style={{ position: "relative" }} onMouseLeave={hide}>
      <svg width={lw + bw + 10} height={rows.length * rh + 6}>
        {rows.map((r, i) => {
          let left = 0;
          return (
            <g key={r.plan} transform={`translate(0, ${i * rh})`}>
              <text x={lw - 12} y={20} textAnchor="end" fontSize={14.5} fill="#4b4a44">{r.plan}</text>
              {parts.map(([k, lab, c]) => {
                const v = r[k] as number, x = lw + left * bw;
                left += v;
                return (
                  <g key={k} onMouseMove={(e) => show(e, <><b>{r.plan}</b> ({r.passages} passages)<br />{lab}: {pct(v)}{k === "repeated" && r.repeated_from ? <><br />from {r.repeated_from}</> : null}</>)}>
                    <rect x={x} y={3} width={Math.max(0, v * bw - 2)} height={rh - 7} fill={c} rx={2} />
                    {v >= 0.1 && <text x={x + (v * bw) / 2} y={20} textAnchor="middle" fontSize={13} fill={c === "#cde2fb" ? "#15140f" : "#fff"} pointerEvents="none">{pct(v)}</text>}
                  </g>
                );
              })}
            </g>
          );
        })}
      </svg>
      <div className="row small" style={{ gap: 22, marginTop: 6 }}>
        {parts.map(([k, lab, c]) => <Key key={k} swatch={c}>{lab}</Key>)}
      </div>
      {node}
    </div>
  );
}

// ---------------------------------------------------------------- t-SNE map
type Pt = [number, number, string, string, number, string, number, string];
export function PassageMap() {
  const { box, show, hide, node } = useTip();
  const pts = tsneData.points as unknown as Pt[];
  const [mode, setMode] = useState<"era" | "theme">("era");
  const [era, setEra] = useState("1960s");
  const [theme, setTheme] = useState("Pedestrian circulation");
  const W = 900, H = 640;
  const { sx, sy } = useMemo(() => {
    const xs = pts.map((p) => p[0]), ys = pts.map((p) => p[1]);
    const [a, b, c, d] = [Math.min(...xs), Math.max(...xs), Math.min(...ys), Math.max(...ys)];
    return { sx: (v: number) => 12 + ((v - a) / (b - a)) * (W - 24), sy: (v: number) => 12 + ((v - c) / (d - c)) * (H - 24) };
  }, [pts]);
  const on = (p: Pt) => (mode === "era" ? p[2] === era : p[5] === theme);
  const count = pts.filter(on).length;
  const order = [...pts].sort((a, b) => Number(on(a)) - Number(on(b)));
  return (
    <div ref={box} className="row" style={{ position: "relative", gap: 36 }} onMouseLeave={hide}>
      <svg width={W} height={H}>
        {order.map((p, i) => {
          const hit = on(p);
          return <circle key={i} cx={sx(p[0])} cy={sy(p[1])} r={hit ? 4.6 : 3.2} fill={hit ? "#1c5cab" : "#d4d1c7"}
            stroke={hit ? "#fdfcf9" : "none"} strokeWidth={0.8}
            onMouseMove={(e) => show(e, <><b>{p[3]}</b>, p. {p[4]}<br /><span style={{ opacity: .75 }}>{p[5]} · cluster: {tsneData.clusters[p[6]]}</span><br />“{p[7]}”</>)} />;
        })}
      </svg>
      <div className="col grow">
        <div className="chips">
          <button className={`chip ${mode === "era" ? "on" : ""}`} onClick={() => setMode("era")}>Highlight a period</button>
          <button className={`chip ${mode === "theme" ? "on" : ""}`} onClick={() => setMode("theme")}>Highlight a theme</button>
        </div>
        <div className="chips mt-m">
          {mode === "era"
            ? tsneData.eras.map((e) => <button key={e} className={`chip ${e === era ? "on" : ""}`} onClick={() => setEra(e)}>{e}</button>)
            : THEMES.filter((t) => (CHECK[t] ?? 0) >= 4).map((t) => <button key={t} className={`chip ${t === theme ? "on" : ""}`} onClick={() => setTheme(t)}>{t}</button>)}
        </div>
        <p className="figure-big mt-l">{count.toLocaleString()}</p>
        <p className="stat-label">of 1,704 passages. Nearby dots are close in meaning; hover one to read it.</p>
        <p className="note mt-auto">t-SNE of bge-base-en-v1.5 embeddings. Neighbourhoods, not distances.</p>
      </div>
      {node}
    </div>
  );
}

// ---------------------------------------------------------------- evaluation grid
type Ev = { id: string; kind: string; retrieval_rank: number | string; runs: number; found: number; cited: number; facts: number; grounded: number; declined: number };
export function EvalGrid() {
  const { box, show, hide, node } = useTip();
  const q = new Map((ragQuestions as { id: string; question: string }[]).map((x) => [x.id, x.question]));
  const rows = ragEval as Ev[];
  const cols: [keyof Ev, string][] = [["found", "Evidence found"], ["facts", "Right fact"], ["cited", "Right citation"]];
  const rh = 27, lw = 200, cw = 150;
  return (
    <div ref={box} style={{ position: "relative", width: lw + cols.length * cw, flexShrink: 0 }} onMouseLeave={hide}>
      <svg width={lw + cols.length * cw} height={rows.length * rh + 44}>
        {cols.map(([, lab], j) => <text key={lab} x={lw + j * cw + cw / 2} y={16} textAnchor="middle" fontSize={14} fill="#4b4a44">{lab}</text>)}
        {rows.map((r, i) => {
          const unans = r.kind === "absent", change = r.kind === "over_time";
          return (
            <g key={r.id} transform={`translate(0, ${36 + i * rh})`} onMouseMove={(e) => show(e, <><b>{r.id}</b> ({r.kind.replace("_", " ")})<br />{q.get(r.id)}</>)}>
              <text x={0} y={16} fontSize={14.5} fill={unans || change ? "#8a877e" : "#15140f"} className="mono">{r.id}</text>
              {change && <text x={lw + cw / 2 - 30} y={16} fontSize={14} fill={r.id.startsWith("parking") ? "#b8322f" : "#4b4a44"}>
                read by hand: {r.id.startsWith("parking") ? "0 of 3 acceptable" : "3 of 3 partly supported"}</text>}
              {!change && cols.map(([k], j) => {
                const v = k === "facts" && unans ? r.declined : (r[k] as number);
                const na = unans && k !== "facts";
                return [0, 1, 2].map((n) => (
                  <circle key={`${k}${n}`} cx={lw + j * cw + cw / 2 + (n - 1) * 24} cy={11} r={8}
                    fill={na ? "none" : n < v ? (k === "facts" ? "#1c5cab" : "#3987e5") : "#fdfcf9"}
                    stroke={na ? "#dcd8cc" : n < v ? "none" : "#b8322f"} strokeWidth={1.6} strokeDasharray={na ? "2 3" : undefined} />
                ));
              })}
            </g>
          );
        })}
      </svg>
      <p className="note">Each dot is one of three runs. Filled = passed, red ring = failed, dashed = does not apply. For the three unanswerable questions the middle column is "declined".</p>
      {node}
    </div>
  );
}
