import type { ReactNode } from "react";
import { R, useStep, type SlideDef } from "./deck";
import { ArchiveTimeline, CerChart, EvalGrid, PassageMap, SimilarityMatrix, ThemeHeatmap, TwoThemes } from "./charts";
import { DemoReplay, OcrExamples, TypedBeside } from "./interactive";

const START = "Start";
const OCR = "OCR";
const CORPUS = "Corpus";
const SEM = "Semantics";
const RAG = "Assistant";
const END = "Findings";

function Stat({ n, children, big }: { n: ReactNode; children: ReactNode; big?: boolean }) {
  return (
    <div>
      <div className={big ? "figure-big" : "figure-mid"}>{n}</div>
      <div className="stat-label">{children}</div>
    </div>
  );
}

/** A route of stations on one line; each station appears at its step. */
function Route({ stations, at }: { stations: [string, string, string][]; at: number[] }) {
  const step = useStep();
  const shown = at.filter((a) => step >= a).length;
  const n = stations.length, w = 100 / n;
  return (
    <div className="line-wrap">
      <div className="line-base" style={{ left: 17, width: `calc(${(n - 1) * w}% )` }} />
      <div className="line-fill" style={{ left: 17, width: `calc(${Math.max(0, shown - 1) * w}%)` }} />
      <div className="stations">
        {stations.map(([name, big, sub], i) => (
          <div key={name} className={`station ${i < shown ? "on" : "off"} ${i === shown - 1 ? "now" : ""}`}>
            <div className="dot" />
            <h3>{name}</h3>
            <div className="big">{big}</div>
            <p>{sub}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

function Claim() {
  const s = useStep();
  const x = (t: string) => <span className={s >= 1 ? "bad" : "plain"}>{t}</span>;
  return (
    <p className="claim">“The 1961 Development Plan proposed tuition of {x("$")}1,250 {x("per year")} for graduate students.”</p>
  );
}

export const slides: SlideDef[] = [
  // ============================================================ start
  {
    id: "title", part: START, title: "Title",
    render: () => (
      <>
        <div className="only-print title-field" />
        <img className="title-bg" src="img/1948_physical_dev_report_p0005_b05.jpg" alt="" />
        <div className="years">1948<br />2018</div>
        <div className="only-aid stamp" style={{ left: 1010, top: 520 }}>Received<br /><span style={{ fontSize: 34 }}>Nov 22 2026</span><br />University Archives</div>
        <div className="only-aid pencil" style={{ left: 1130, top: 330, fontSize: 46, transform: "rotate(6deg)" }}>OCR, themes,<br />&amp; a chatbot<br />that cites ↙</div>
        <p className="note" style={{ position: "relative", fontSize: 18 }}>AI for Urban Sustainability · Final project · 2026</p>
        <h1 style={{ marginTop: "auto", position: "relative", maxWidth: 1050 }}>Reading seventy years of Penn's campus plans</h1>
        <p className="lede" style={{ position: "relative", maxWidth: 900 }}>OCR, semantic analysis and a local assistant that cites its pages.</p>
        <p className="body mt-m" style={{ position: "relative" }}>Zhanchao Yang</p>
      </>
    ),
  },
  {
    id: "questions", part: START, title: "Questions", steps: 2,
    render: () => (
      <>
        <h2 style={{ marginBottom: 44 }}>Three questions</h2>
        {[
          ["Can open-source OCR read the archive, and does fine-tuning help?", "scored against text typed by a person"],
          ["How did the plans' concerns change from 1948 to 2018?", "embeddings of every passage"],
          ["Can a local assistant answer with page citations?", "and where does it go wrong"],
        ].map(([q, how], i) => (
          <R key={q} at={i} className="numline">
            <span className="n">{i + 1}</span>
            <div><h3>{q}</h3><p>{how}</p></div>
          </R>
        ))}
      </>
    ),
  },
  {
    id: "archive", part: START, title: "The archive",
    render: () => (
      <>
        <h2>17 plans, and two long silences</h2>
        <p className="lede">Scans until 1998; Penn Connects (2006–2018) is born-digital. Hover a bar.</p>
        <div className="mt-auto" style={{ marginBottom: 30 }}><ArchiveTimeline /></div>
      </>
    ),
  },
  {
    id: "pipeline", part: START, title: "Pipeline", steps: 3,
    render: () => (
      <>
        <h2>From scanned page to cited answer</h2>
        <Route at={[0, 0, 1, 1, 2, 3]} stations={[
          ["Scan", "1,787 pages", "17 plans, 33 PDFs"],
          ["Read", "PP-OCRv6", "open-source OCR, laptop CPU"],
          ["Check", "92 paragraphs", "typed by hand, blind"],
          ["Clean", "1,754 passages", "page review, prose filter"],
          ["Compare", "12 themes", "embeddings, similarity"],
          ["Ask", "18 questions", "local RAG with citations"],
        ]} />
        <p className="note mt-auto">Each stage is measured before the next one uses it. Nothing leaves the laptop.</p>
      </>
    ),
  },

  // ============================================================ OCR
  {
    id: "typed", part: OCR, title: "Ground truth", steps: 1,
    render: () => (
      <>
        <h2 style={{ marginBottom: 40 }}>First, a person types the page</h2>
        <TypedBeside index={2} />
        <R at={1} className="row mt-auto" style={{ gap: 90, marginBottom: 10 }}>
          <Stat n="92">paragraphs typed, 33 kept for testing</Stat>
          <Stat n="0.7 %">two people typing the same paragraph disagree this much</Stat>
        </R>
      </>
    ),
  },
  {
    id: "cer", part: OCR, title: "Fine-tuning", steps: 2,
    render: () => (
      <>
        <h2>Fine-tuning ties the pretrained model</h2>
        <div className="row mt-l" style={{ gap: 90 }}>
          <CerChart />
          <div className="col grow" style={{ gap: 40 }}>
            <Stat big n="77 · 76">character errors in 12,203 on unseen pages: pretrained · fine-tuned</Stat>
            <R at={1}><p className="small" style={{ fontSize: 20 }}>Training only worked after fixing a pooling bug in PP-OCRv6's training mode (24 % → 100 % before any update).</p></R>
            <R at={2}><h3 style={{ fontSize: 40 }}>So the corpus is read with the <em className="hl">pretrained</em> model.</h3>
              <p className="only-aid pencil" style={{ position: "static", fontSize: 38, marginTop: 8 }}>same accuracy, nothing to retrain ✓</p></R>
          </div>
        </div>
      </>
    ),
  },
  {
    id: "examples", part: OCR, title: "OCR errors",
    render: () => (
      <>
        <h2 style={{ marginBottom: 32 }}>The error that matters is a lost line</h2>
        <OcrExamples />
        <p className="note mt-auto">168 of 173 dates, numbers and names are read exactly. Lost text causes about 62 of the 77 test errors.</p>
      </>
    ),
  },

  // ============================================================ corpus
  {
    id: "corpus", part: CORPUS, title: "Corpus", steps: 4,
    render: () => {
      const lines: [string, string, string, number][] = [
        ["", "1,787", "pages, 1948–2018", 0],
        ["−", "447", "maps, covers, handwriting: 471 doubtful pages read by hand", 1],
        ["−", "", "labels, headers, page numbers: a prose filter", 2],
        ["−", "", "second scans of 1961, 1963 and 1966", 3],
      ];
      return (
        <>
          <h2>From pages to passages</h2>
          <div className="ledger mt-l">
            {lines.map(([op, amt, what, at]) => (
              <R key={what} at={at} className="ln"><span className="op">{op}</span><span className="amt">{amt}</span><span className="what">{what}</span></R>
            ))}
            <R at={4} className="ln total"><span className="op">=</span><span className="amt">1,754</span><span className="what">passages of about 1,000 characters, each with plan, year and page</span></R>
          </div>
        </>
      );
    },
  },

  // ============================================================ semantics
  {
    id: "map", part: SEM, title: "Passage map",
    render: () => (
      <>
        <h2 style={{ marginBottom: 28 }}>Every passage on one map</h2>
        <PassageMap />
      </>
    ),
  },
  {
    id: "lineage", part: SEM, title: "Plan similarity",
    render: () => (
      <>
        <h2>The plans form lineages</h2>
        <p className="lede" style={{ marginBottom: 28 }}>1961 → 1963 → 1966 revise one text; 1992 leads into Penn Connects. Click a plan.</p>
        <SimilarityMatrix />
      </>
    ),
  },
  {
    id: "themes", part: SEM, title: "Themes",
    render: () => (
      <>
        <h2 style={{ marginBottom: 28 }}>What each period writes about</h2>
        <ThemeHeatmap />
        <p className="note mt-auto">Click a theme. Grey rows failed the hand check (3 of 5 or fewer right) and are not interpreted.</p>
      </>
    ),
  },
  {
    id: "parking", part: SEM, title: "Parking and pedestrians", steps: 1,
    render: () => (
      <>
        <h2>Parking holds steady; walking grows from 1977</h2>
        <div className="row mt-l" style={{ gap: 90 }}>
          <TwoThemes W={820} H={540} />
          <div className="col grow" style={{ gap: 44 }}>
            <Stat n="3–7 %">of every period's passages are about parking</Stat>
            <Stat n="4–7 % → 10–17 %">pedestrian circulation, in most plans after 1977</Stat>
            <p className="only-aid pencil" style={{ position: "static", fontSize: 40, color: "var(--penn-blue)" }}>walking ↗ after the 1977 landscape plan</p>
            <R at={1}><p className="small" style={{ fontSize: 20 }}>Shares measure attention, not position: a plan arguing against parking still counts toward parking.</p></R>
          </div>
        </div>
      </>
    ),
  },

  // ============================================================ assistant
  {
    id: "rag", part: RAG, title: "Assistant", steps: 3,
    render: () => (
      <>
        <h2>An assistant that has to show its sources</h2>
        <Route at={[0, 0, 1, 2, 3]} stations={[
          ["Ask", "a question", "“How many parking spaces did the 1961 plan project?”"],
          ["Plan", "llama3.1:8b", "chooses its searches and years"],
          ["Retrieve", "ChromaDB", "bge vectors, year and draft filters"],
          ["Answer", "[1] [2] [3]", "only from numbered passages"],
          ["Check", "the scan", "cited pages open beside the answer"],
        ]} />
        <p className="note mt-auto">Ollama on one laptop · 10.8 s per answer on average.</p>
      </>
    ),
  },
  {
    id: "demo", part: RAG, title: "Recorded runs",
    render: () => (
      <>
        <h2 style={{ fontSize: 48, marginBottom: 22 }}>Six recorded runs, each checked by hand</h2>
        <div style={{ flex: 1, minHeight: 0 }}><DemoReplay /></div>
      </>
    ),
  },
  {
    id: "eval", part: RAG, title: "Evaluation", steps: 1,
    render: () => (
      <>
        <h2 style={{ marginBottom: 30 }}>18 questions, three runs each</h2>
        <div className="row" style={{ gap: 90 }}>
          <EvalGrid />
          <div className="col grow" style={{ gap: 30 }}>
            <Stat n="37 / 39">runs found the source page</Stat>
            <Stat n="34 / 39">answers had the right fact</Stat>
            <Stat n="30 / 39">cited the passage that holds it</Stat>
            <R at={1} className="row" style={{ gap: 56 }}>
              <Stat n={<span style={{ fontSize: 44 }}>6 / 9</span>}>unanswerable, declined</Stat>
              <Stat n={<span style={{ fontSize: 44, color: "var(--bad)" }}>0 / 3</span>}>parking across decades</Stat>
            </R>
          </div>
        </div>
      </>
    ),
  },
  {
    id: "failure", part: RAG, title: "A failure", steps: 2, dark: true,
    render: () => (
      <>
        <p className="note" style={{ fontSize: 20 }}>Asked “What tuition did the 1961 plan propose?” · 3 of 3 runs</p>
        <div className="mt-l"><Claim /></div>
        <R at={1} className="mt-l">
          <p className="note" style={{ marginBottom: 10 }}>What passage [6] actually is: Table I, Existing and Projected Student <b>Enrollment</b>, 1960–70, p. 25 (OCR)</p>
          <p className="only-aid pencil" style={{ left: 1150, top: 330, fontSize: 48, transform: "rotate(-4deg)" }}>enrolment, not dollars!</p>
          <p className="table-ocr">… (3,190) (<mark>1,060</mark>) ( 900) (1,325) 4,250 2,225 6,475 (3,750) (<mark>1,250</mark>) (2,200) ( 600) …{"\n"}Graduate &amp; Professional 3,480 3,800 4,200 20.6</p>
        </R>
        <R at={2} className="mt-auto" style={{ marginBottom: 20 }}>
          <h3 style={{ fontSize: 40, maxWidth: 1200 }}>The automatic check passed: 1,250 is in the source. A number that appears is not a sentence that is supported.</h3>
        </R>
      </>
    ),
  },

  // ============================================================ findings
  {
    id: "end", part: END, title: "Findings", steps: 3,
    render: () => (
      <>
        <h2 style={{ marginBottom: 36 }}>What we found</h2>
        {[
          ["0.63 %", "Pretrained open-source OCR is enough", "below the gap between two human typists; the risk left is a silently lost line"],
          ["1977", "The plans' attention moves by period", "1960s plans revise one text; pedestrian space grows after 1977, parking stays flat"],
          ["34 / 39", "The assistant finds the facts, not always the proof", "it invents figures under a false premise; a citation still needs reading"],
        ].map(([n, h, p], i) => (
          <R key={h} at={i} className="numline" style={{ gridTemplateColumns: "300px 1fr" }}>
            <span className="n" style={{ fontSize: 76, color: "var(--penn-blue)" }}>{n}</span>
            <div><h3>{h}</h3><p>{p}</p></div>
          </R>
        ))}
        <R at={3} className="row mt-auto" style={{ alignItems: "baseline", justifyContent: "space-between" }}>
          <h3 style={{ fontSize: 44 }}>Thank you</h3>
          <span className="mono small">github.com/zyang91/ai-sustainbility-final</span>
        </R>
      </>
    ),
  },
];
