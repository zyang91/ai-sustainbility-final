import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useLayoutEffect,
  useState,
  type CSSProperties,
  type ReactNode,
} from "react";

/** One slide. `steps` is how many times "next" reveals something before moving on. */
export interface SlideDef {
  id: string;
  part: string;
  title: string;
  steps?: number;
  dark?: boolean;
  render: () => ReactNode;
}

export const W = 1600;
export const H = 900;

const StepCtx = createContext(0);
export const useStep = () => useContext(StepCtx);

/** Shown from step `at` on. Keeps its space before, so nothing jumps. */
export function R({ at, children, inline, style, className }: {
  at: number; children: ReactNode; inline?: boolean; style?: CSSProperties; className?: string;
}) {
  const on = useStep() >= at;
  const Tag = inline ? "span" : "div";
  return (
    <Tag className={`reveal ${on ? "in" : ""} ${className ?? ""}`} style={style} aria-hidden={!on}>
      {children}
    </Tag>
  );
}

/** The three looks: an archive folder, a diazo blueprint, a 1960s printed plan. */
export const THEMES_LOOK = [
  { id: "aid", name: "Folder" },
  { id: "blueprint", name: "Blueprint" },
  { id: "print", name: "Print" },
] as const;
type Look = (typeof THEMES_LOOK)[number]["id"];

function savedLook(): Look {
  try {
    const v = localStorage.getItem("deck-look");
    if (THEMES_LOOK.some((t) => t.id === v)) return v as Look;
  } catch { /* storage blocked: use the default */ }
  return "aid";
}

function readHash(n: number): [number, number] {
  const m = location.hash.match(/^#\/(\d+)(?:\/(\d+))?/);
  if (!m) return [0, 0];
  return [Math.min(Math.max(+m[1] - 1, 0), n - 1), +(m[2] ?? 0)];
}

export function Deck({ slides }: { slides: SlideDef[] }) {
  const [[index, step], setPos] = useState<[number, number]>(() => readHash(slides.length));
  const [scale, setScale] = useState(1);
  const [look, setLookState] = useState<Look>(savedLook);
  const setLook = (l: Look) => {
    setLookState(l);
    try { localStorage.setItem("deck-look", l); } catch { /* not saved; fine */ }
  };
  const steps = (i: number) => slides[i].steps ?? 0;

  useLayoutEffect(() => {
    const fit = () => setScale(Math.min(innerWidth / W, (innerHeight - 0) / H));
    fit();
    addEventListener("resize", fit);
    return () => removeEventListener("resize", fit);
  }, []);

  useEffect(() => {
    const want = `#/${index + 1}${step ? `/${step}` : ""}`;
    if (location.hash !== want) history.replaceState(null, "", want);
    document.title = `${slides[index].title} · Reading Penn's Campus Plans`;
  }, [index, step, slides]);

  const next = useCallback(() => setPos(([i, s]) =>
    s < steps(i) ? [i, s + 1] : i < slides.length - 1 ? [i + 1, 0] : [i, s]), [slides]);
  const prev = useCallback(() => setPos(([i, s]) =>
    s > 0 ? [i, s - 1] : i > 0 ? [i - 1, steps(i - 1)] : [i, s]), [slides]);
  const go = (i: number) => setPos([i, 0]);

  useEffect(() => {
    const key = (e: KeyboardEvent) => {
      const t = e.target as HTMLElement;
      if (t.closest("input, textarea, select")) return;
      if ((e.key === " " || e.key === "Enter") && t.closest("button")) return;
      if (["ArrowRight", "ArrowDown", "PageDown", " "].includes(e.key)) { e.preventDefault(); next(); }
      else if (["ArrowLeft", "ArrowUp", "PageUp"].includes(e.key)) { e.preventDefault(); prev(); }
      else if (e.key === "Home") go(0);
      else if (e.key === "End") go(slides.length - 1);
      else if (e.key === "t") setLookState((l) => {
        const nx = THEMES_LOOK[(THEMES_LOOK.findIndex((t) => t.id === l) + 1) % THEMES_LOOK.length].id;
        try { localStorage.setItem("deck-look", nx); } catch { /* not saved */ }
        return nx;
      });
      else if (e.key === "f") document.fullscreenElement ? document.exitFullscreen() : document.documentElement.requestFullscreen();
    };
    const hash = () => setPos(readHash(slides.length));
    addEventListener("keydown", key);
    addEventListener("hashchange", hash);
    return () => { removeEventListener("keydown", key); removeEventListener("hashchange", hash); };
  }, [next, prev, slides.length]);

  const slide = slides[index];
  const parts = [...new Set(slides.map((s) => s.part))];
  const partNo = parts.indexOf(slide.part) + 1;
  const pad = (n: number) => String(n).padStart(2, "0");

  return (
    <div className="viewport">
      <div className={`stage th-${look} ${slide.dark ? "dark" : ""}`} style={{ width: W, height: H, transform: `translate(-50%, -50%) scale(${scale})` }}>
        <div className="decor" aria-hidden>
          <div className="folder"><div className="tab">UPJ 9.4 · Box 1 · Folder {partNo} · {slide.part}</div></div>
          <div className="sheet"><i className="hole" /><i className="hole" /></div>
          <div className="frame-line" />
          <div className="runhead"><span>University of Pennsylvania · Campus Plans 1948–2018</span><span>{pad(partNo)} {slide.part}</span></div>
        </div>
        <StepCtx.Provider value={step}>
          <section className={`slide slide-${slide.id}`} key={slide.id}>
            {slide.render()}
          </section>
        </StepCtx.Provider>
        <footer className="deck-foot">
          <nav className="route" aria-label="Sections">
            {parts.map((p) => {
              const first = slides.findIndex((s) => s.part === p);
              return (
                <div key={p} className="leg">
                  <button className={`leg-name ${slide.part === p ? "cur" : ""}`} onClick={() => go(first)}>{p}</button>
                  {slides.map((s, i) => s.part !== p ? null : (
                    <button key={s.id} aria-label={s.title} title={s.title} onClick={() => go(i)}
                      className={`stop ${i === index ? "cur" : i < index ? "past" : ""}`} />
                  ))}
                </div>
              );
            })}
          </nav>
          <div className="looks" role="group" aria-label="Look (t)">
            {THEMES_LOOK.map((t) => (
              <button key={t.id} className={`look ${look === t.id ? "on" : ""}`} onClick={() => setLook(t.id)} title="Switch look (t)">{t.name}</button>
            ))}
          </div>
          <span className="pager">{pad(index + 1)} / {slides.length}</span>
          <div className="tblock">
            <div><small>Project</small>Penn campus plans</div>
            <div><small>Section</small>{slide.part}</div>
            <div><small>Sheet</small>{pad(index + 1)} / {slides.length}</div>
          </div>
        </footer>
      </div>
    </div>
  );
}
