import { useState } from "react";
import {
  ArrowLeftRight,
  Check,
  Copy,
  LoaderCircle,
  Search,
  X,
} from "lucide-react";

const INITIAL_PROJECTS = [
  "100 Main St",
  "2460 N Australian Ave",
  "500 Broadway",
  "Hospital Phase 1",
  "Hospital Phase 2",
];

const PHASES = [
  { key: "normalization", label: "Normalization" },
  { key: "word_overlap", label: "Word Overlap" },
  { key: "text_similarity", label: "Textual Match" },
  { key: "identifier_compatibility", label: "Identifiers" },
  { key: "noise_retention", label: "Noise Retention" },
];

const ABBREVIATIONS = {
  n: "north",
  s: "south",
  e: "east",
  w: "west",
  ave: "avenue",
  st: "street",
  blvd: "boulevard",
  rd: "road",
  dr: "drive",
};

function normalizeToken(token) {
  const cleaned = token.toLowerCase().replace(/[^a-z0-9]/g, "");
  return ABBREVIATIONS[cleaned] ?? cleaned;
}

function getTokens(value) {
  return value.trim().split(/\s+/).filter(Boolean);
}

export default function App() {
  const [dirtyName, setDirtyName] = useState("2460 North Australian");
  const knownProjects = INITIAL_PROJECTS;
  const [bestMatch, setBestMatch] = useState(null);
  const [confidenceScore, setConfidenceScore] = useState(null);
  const [matchMetrics, setMatchMetrics] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const [copyLabel, setCopyLabel] = useState("Copy match");

  const incomingTokens = getTokens(dirtyName);
  const normalizedIncoming = new Set(incomingTokens.map(normalizeToken));
  const matchTokens = getTokens(bestMatch ?? "");
  const sharedTokens = matchTokens.filter((token) =>
    normalizedIncoming.has(normalizeToken(token)),
  );
  const score = confidenceScore === null ? 0 : Math.max(0, Math.min(100, confidenceScore));
  const scoreColor = bestMatch ? "#ff394b" : "#70747d";
  const scoreOffset = 792 - (792 * score) / 100;
  const numericInput = dirtyName.match(/\d+/)?.[0] ?? "—";
  const numericMatch = bestMatch?.match(/\d+/)?.[0] ?? "—";
  const allTokens = [...incomingTokens, ...matchTokens];
  const abbreviationPair = allTokens.reduce((foundPair, token) => {
    if (foundPair) return foundPair;
    const expanded = ABBREVIATIONS[token.toLowerCase()];
    if (!expanded) return null;
    const matchingLongForm = allTokens.find(
      (candidate) => normalizeToken(candidate) === expanded && candidate.toLowerCase() !== token.toLowerCase(),
    );
    return matchingLongForm ? { long: expanded, short: token } : null;
  }, null);

  async function handleSearch(event) {
    event.preventDefault();
    if (!dirtyName.trim() || knownProjects.length === 0) {
      setError("Enter a project name and provide at least one official project.");
      return;
    }

    setIsLoading(true);
    setError("");
    setMatchMetrics(null);

    try {
      const response = await fetch("http://127.0.0.1:8000/api/match", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          dirty_name: dirtyName,
          known_projects: knownProjects,
          threshold: 80.0,
        }),
      });

      if (!response.ok) {
        throw new Error(`Matcher API returned ${response.status}.`);
      }

      const result = await response.json();
      setBestMatch(result.best_match);
      setConfidenceScore(Number(result.confidence_score ?? 0));
      setMatchMetrics(result.metrics ?? null);
    } catch (requestError) {
      setBestMatch(null);
      setConfidenceScore(null);
      setMatchMetrics(null);
      setError(
        requestError instanceof Error
          ? requestError.message
          : "Could not connect to the matcher API.",
      );
    } finally {
      setIsLoading(false);
    }
  }

  async function handleCopyMatch() {
    if (!bestMatch) return;
    try {
      await navigator.clipboard.writeText(bestMatch);
      setCopyLabel("Copied");
      window.setTimeout(() => setCopyLabel("Copy match"), 1400);
    } catch {
      setError("Clipboard access is unavailable in this browser context.");
    }
  }

  const alternatives = knownProjects.filter((project) => project !== bestMatch).slice(0, 2);

  return (
    <main className="flex min-h-screen items-start justify-center bg-[#0d0e11] px-3 py-4 text-[#e3e2e6] sm:items-center sm:px-6 sm:py-8">
      <div className="flex w-full max-w-5xl flex-col gap-5 rounded-2xl border border-[#292a2d] bg-[#1b1b1f] p-4 sm:p-6">
        <header className="flex w-full flex-col items-stretch justify-between gap-3 border-b border-[#343538]/70 pb-4 sm:flex-row sm:items-center">
          <form onSubmit={handleSearch} className="relative w-full sm:max-w-md">
            <label className="sr-only" htmlFor="dirty-project-name">Dirty project name</label>
            <Search aria-hidden="true" className="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 text-[#8e9193]" size={17} />
            <input
              id="dirty-project-name"
              type="text"
              value={dirtyName}
              onChange={(event) => setDirtyName(event.target.value)}
              placeholder="Enter project or address name..."
              className="h-11 w-full rounded-xl border border-[#292a2d] bg-[#1f1f23] py-2 pl-10 pr-12 text-sm text-[#f1f3f5] outline-none transition-colors placeholder:text-[#777b82] focus:border-[#8e9193]"
            />
            <button
              type="submit"
              disabled={isLoading}
              aria-label="Search project names"
              title="Search project names"
              className="absolute right-1.5 top-1/2 grid size-8 -translate-y-1/2 place-items-center rounded-lg text-[#8e9193] transition-colors hover:bg-[#343538] hover:text-white disabled:opacity-50"
            >
              {isLoading ? <LoaderCircle className="animate-spin" size={16} /> : <Search size={16} />}
            </button>
          </form>

        </header>

        {error && (
          <div role="alert" className="flex items-start gap-2 rounded-lg border border-red-900/70 bg-red-950/30 px-3 py-2.5 text-xs leading-5 text-red-200">
            <X className="mt-0.5 shrink-0" size={15} />
            <span>{error} Keep the FastAPI server running at 127.0.0.1:8000.</span>
          </div>
        )}

        <div className="grid grid-cols-1 items-stretch gap-5 lg:grid-cols-12">
          <section className="flex flex-col justify-between gap-4 lg:col-span-7" aria-label="Candidate diagnostics">
            <article className="relative flex min-h-[272px] flex-col justify-between overflow-hidden rounded-xl border border-[#292a2d] bg-[#121316] p-5">
              <div className="flex items-center justify-between gap-3 font-mono text-[10px] text-[#8e9193]">
                <span className="flex items-center gap-1.5 uppercase">
                  <span className={`size-1.5 rounded-full ${bestMatch ? "bg-[#f1f3f5]" : "bg-[#6a6d74]"}`} />
                  Top candidate
                </span>
                <span className="text-right">LEVENSHTEIN + JACCARD</span>
              </div>

              <div className="my-6 flex w-full flex-col items-center justify-center">
                <div className="relative flex h-[78px] w-full max-w-[380px] items-center justify-center">
                  <svg className="pointer-events-none absolute inset-0 h-full w-full" viewBox="0 0 380 78" fill="none" aria-hidden="true">
                    <defs>
                      <filter id="capsule-shadow" x="-20%" y="-30%" width="140%" height="160%">
                        <feGaussianBlur stdDeviation="3" />
                      </filter>
                    </defs>
                    <rect x="4" y="4" width="372" height="70" rx="35" fill="#0b0c0e" stroke="#1c1d22" strokeWidth="2" />
                    <rect x="8" y="8" width="364" height="62" rx="31" stroke="#262830" strokeWidth="4.5" />
                    {score > 0 && (
                      <>
                        <rect x="8" y="8" width="364" height="62" rx="31" pathLength="792" stroke={scoreColor} strokeWidth="4.5" strokeDasharray="792" strokeDashoffset={scoreOffset} strokeLinecap="round" opacity="0.75" filter="url(#capsule-shadow)" />
                        <rect x="8" y="8" width="364" height="62" rx="31" pathLength="792" stroke={scoreColor} strokeWidth="4.5" strokeDasharray="792" strokeDashoffset={scoreOffset} strokeLinecap="round" />
                      </>
                    )}
                  </svg>
                  <div className="relative z-10 flex select-none items-baseline justify-center gap-2.5 px-6">
                    <span className="font-sans text-[36px] font-bold leading-none text-white sm:text-[40px]">
                      {confidenceScore === null ? "--" : `${Math.round(confidenceScore)}%`}
                    </span>
                    <span className="text-sm font-medium text-[#9ca1ab]">Match</span>
                  </div>
                </div>

                <div className="mt-4 flex max-w-full items-center gap-2 rounded-lg border border-[#343538]/70 bg-[#28292d]/70 px-3 py-2 sm:px-4">
                  <span className="shrink-0 font-mono text-[9px] text-[#8e9193] sm:text-[10px]">MATCHED STRING:</span>
                  <span className="min-w-0 break-words text-xs font-medium text-[#f1f3f5] sm:text-sm">
                    {bestMatch ?? "Search to find a project"}
                  </span>
                  <button
                    type="button"
                    onClick={handleCopyMatch}
                    disabled={!bestMatch}
                    title={copyLabel}
                    aria-label={copyLabel}
                    className="ml-1 shrink-0 text-[#8e9193] transition-colors hover:text-white disabled:cursor-not-allowed disabled:opacity-40"
                  >
                    <Copy size={14} />
                  </button>
                </div>
              </div>

              <div className="flex items-start justify-between gap-3 border-t border-[#343538]/50 pt-3 font-mono text-[9px] text-[#8e9193] sm:text-[10px]">
                <span className="min-w-0 break-words">QUERY: &quot;{dirtyName || "—"}&quot;</span>
                <span className="shrink-0">{bestMatch ? "MATCHED" : "READY"}</span>
              </div>
            </article>

            <article className="rounded-xl border border-[#292a2d] bg-[#121316] p-4">
              <div className="mb-3 flex items-center justify-between gap-3 font-mono text-[10px] text-[#8e9193]">
                <span>TOKEN DECOMPOSITION</span>
                <span>{sharedTokens.length} OF {matchTokens.length || incomingTokens.length} MATCHED</span>
              </div>
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                <div className="flex flex-col gap-2 rounded-lg border border-[#292a2d] bg-[#1f1f23] p-3">
                  <div className="flex items-center justify-between gap-2 font-mono text-[9px] text-[#c4c7c9] sm:text-[10px]">
                    <span>ABBREVIATION EXPANSION</span><span className="text-[#f1f3f5]">{abbreviationPair ? "98%" : "—"}</span>
                  </div>
                  <div className="flex items-center gap-2 text-xs font-medium text-[#f1f3f5]">
                    <span>{abbreviationPair ? abbreviationPair.long : "No abbreviation"}</span>
                    <ArrowLeftRight className="text-[#8e9193]" size={13} />
                    <span>{abbreviationPair ? abbreviationPair.short : "—"}</span>
                  </div>
                  <div className="h-1 overflow-hidden rounded-full bg-[#292a2d]"><div className="h-full rounded-full bg-[#f1f3f5]" style={{ width: abbreviationPair ? "98%" : "0%" }} /></div>
                </div>
                <div className="flex flex-col gap-2 rounded-lg border border-[#292a2d] bg-[#1f1f23] p-3">
                  <div className="flex items-center justify-between gap-2 font-mono text-[9px] text-[#c4c7c9] sm:text-[10px]">
                    <span>NUMERIC EXACTNESS</span><span className="text-[#f1f3f5]">{numericInput !== "—" && numericInput === numericMatch ? "100%" : "—"}</span>
                  </div>
                  <div className="flex items-center gap-2 text-xs font-medium text-[#f1f3f5]">
                    <span>Digits</span>
                    <Check className="text-[#8e9193]" size={13} />
                    <span className="truncate">{numericInput} ↔ {numericMatch}</span>
                  </div>
                  <div className="h-1 overflow-hidden rounded-full bg-[#292a2d]"><div className="h-full rounded-full bg-[#f1f3f5]" style={{ width: numericInput !== "—" && numericInput === numericMatch ? "100%" : "0%" }} /></div>
                </div>
              </div>
              <p className="mt-3 text-right font-mono text-[9px] text-[#686c74]">TOKEN DETAIL IS A UI PREVIEW</p>
            </article>

            <article className="flex flex-col justify-between rounded-xl border border-[#292a2d] bg-[#121316] p-4">
              <div className="mb-2 flex items-center justify-between gap-3 font-mono text-[10px] text-[#8e9193]">
                <span>RUNNER-UPS</span><span>OFFICIAL RECORDS</span>
              </div>
              <div className="flex flex-col gap-1.5">
                {alternatives.length ? alternatives.map((project, index) => (
                  <div key={project} className="flex items-center justify-between gap-3 rounded-lg border border-transparent bg-[#1f1f23]/70 px-3 py-2 text-xs transition-colors hover:border-[#292a2d] hover:bg-[#1f1f23]">
                    <div className="flex min-w-0 items-center gap-2 text-[#c4c7c9]">
                      <span className="shrink-0 font-mono text-[10px] text-[#8e9193]">0{index + 2}</span>
                      <span className="truncate">{project}</span>
                    </div>
                    <span className="shrink-0 font-mono text-[9px] text-[#686c74]">NOT SCORED</span>
                  </div>
                )) : (
                  <div className="rounded-lg bg-[#1f1f23]/70 px-3 py-3 text-xs text-[#8e9193]">Load more official records to see alternatives.</div>
                )}
              </div>
            </article>
          </section>

          <aside className="flex min-w-0 flex-col justify-between rounded-xl border border-[#292a2d] bg-[#121316] p-5 lg:col-span-5">
            <div className="mb-3 flex w-full items-center justify-between gap-3 font-mono text-[10px] text-[#8e9193]">
              <span>PHASE ANALYSIS</span><span>5 PHASES</span>
            </div>
            <div className="my-auto flex flex-col justify-around gap-4 py-2 sm:gap-5">
              {PHASES.map((phase, index) => (
                <div className="flex flex-col gap-1.5" key={phase.label}>
                  {(() => {
                    const value = matchMetrics?.[phase.key];
                    const displayValue = value === undefined
                      ? "—"
                      : phase.key === "identifier_compatibility"
                        ? value === 100 ? "CLEAR" : "CONFLICT"
                        : `${Math.round(value)}%`;
                    return (
                      <>
                  <div className="flex items-center justify-between gap-3 font-mono text-xs">
                    <span className="font-medium text-[#e3e2e6]">{phase.label}</span>
                    <span className="text-[10px] text-[#8e9193]">Phase 0{index + 1}</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <div className="relative flex h-5 flex-1 items-center overflow-hidden rounded-full border border-white/[0.04] bg-[#0e0f12] p-[3px] shadow-[inset_0_3px_6px_rgba(0,0,0,0.75),inset_0_1px_2px_rgba(0,0,0,0.9)]">
                      <div className="h-full rounded-full bg-gradient-to-b from-[#52565e] via-[#2f3237] to-[#1a1b1f] shadow-[0_2px_4px_rgba(0,0,0,0.6),inset_0_1px_1px_rgba(255,255,255,0.35),inset_0_-1px_1px_rgba(0,0,0,0.7)] transition-[width] duration-500" style={{ width: `${value ?? 0}%` }} />
                    </div>
                    <span className="w-16 shrink-0 text-right font-mono text-[10px] font-medium text-[#f1f3f5]">{displayValue}</span>
                  </div>
                      </>
                    );
                  })()}
                </div>
              ))}
            </div>
            <div className="mt-3 flex items-center justify-between gap-3 border-t border-[#343538]/60 pt-3 font-mono text-[9px] text-[#8e9193] sm:text-[10px]">
              <span>SCORE: 80% TEXT + 20% WORDS</span>
              <span className="text-right text-[#c4c7c9]">LIVE CANDIDATE DATA</span>
            </div>
            <p className="mt-2 text-[9px] leading-4 text-[#686c74]">Measurements update from the best catalog candidate after each search.</p>
          </aside>
        </div>
      </div>
    </main>
  );
}