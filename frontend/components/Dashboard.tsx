"use client";
import { useState, useEffect } from "react";
import { Tender, TendersResponse, triggerScrape, fetchTenders, fetchConfigStatus } from "@/lib/api";
import TenderCard from "@/components/TenderCard";
import TenderDetail from "@/components/TenderDetail";
import BriefingPlayer from "@/components/BriefingPlayer";
import KnowledgeBase from "@/components/KnowledgeBase";
import LiveAgentTerminal from "@/components/LiveAgentTerminal";
import {
  Search, SlidersHorizontal, RefreshCw, Globe, Zap,
  TrendingUp, Award, ChevronDown, X, Database, BookOpen, LayoutGrid, FileEdit, AlertTriangle, Trophy
} from "lucide-react";
import { clsx } from "clsx";
import DraftQueue from "@/components/DraftQueue";

/* ── Constants ─────────────────────────────────────── */
const PORTALS = ["All","sam_gov","ted_eu","ungm","find_a_tender","austender","canadabuys"];
const PORTAL_LABELS: Record<string,string> = {
  All:"All", sam_gov:"SAM.gov", ted_eu:"TED EU", ungm:"UNGM",
  find_a_tender:"Find a Tender", austender:"AusTender", canadabuys:"CanadaBuys"
};
const COUNTRIES = ["All","US","UK","EU","CA","AU","UN"];
const SORT_OPTIONS = [
  { label: "Score ↓",    value: "score_desc"   },
  { label: "Deadline ↑", value: "deadline_asc" },
  { label: "Value ↓",   value: "value_desc"   },
  { label: "Win Prob ↓",value: "prob_desc"    },
];

/* ── Filter + sort helper ───────────────────────────── */
function filterAndSort(tenders: Tender[], {
  query, portal, country, scoreMin, sort, enrichedOnly,
}: { query:string; portal:string; country:string; scoreMin:number; sort:string; enrichedOnly:boolean }) {
  let out = [...tenders];
  if (query)        out = out.filter(t => t.title.toLowerCase().includes(query.toLowerCase()) || t.agency.toLowerCase().includes(query.toLowerCase()));
  if (portal  !== "All") out = out.filter(t => t.source_portal === portal);
  if (country !== "All") out = out.filter(t => t.country === country);
  if (scoreMin > 0)      out = out.filter(t => (t.relevance_score ?? 0) >= scoreMin);
  if (enrichedOnly)      out = out.filter(t => t.enriched);
  if (sort === "score_desc")    out.sort((a,b)=>(b.relevance_score??0)-(a.relevance_score??0));
  if (sort === "deadline_asc")  out.sort((a,b)=>(a.days_until_deadline??999)-(b.days_until_deadline??999));
  if (sort === "value_desc")    out.sort((a,b)=>(b.estimated_value??0)-(a.estimated_value??0));
  if (sort === "prob_desc")     out.sort((a,b)=>(b.our_probability??0)-(a.our_probability??0));
  return out;
}

interface Props { initialData: TendersResponse }

export default function Dashboard({ initialData }: Props) {
  const [allTenders, setAllTenders] = useState<Tender[]>(initialData?.tenders ?? []);
  const [selected,   setSelected]   = useState<Tender | null>(null);
  const [query,      setQuery]      = useState("");
  const [portal,     setPortal]     = useState("All");
  const [country,    setCountry]    = useState("All");
  const [scoreMin,   setScoreMin]   = useState(60);
  const [sort,       setSort]       = useState("score_desc");
  const [enrichedOnly, setEnrichedOnly] = useState(false);
  const [isScraping, setIsScraping] = useState(false);
  const [showFilters,setShowFilters]= useState(false);
  const [view,       setView]       = useState<"tenders"|"knowledge"|"drafts">("tenders");
  const companyName = "TechVentures";
  const [configStatus, setConfigStatus] = useState<{ all_configured: boolean; missing_keys: string[]; demo_mode: boolean } | null>(null);

  useEffect(() => {
    fetchConfigStatus().then(setConfigStatus);
  }, []);

  const tenders = filterAndSort(allTenders, { query, portal, country, scoreMin, sort, enrichedOnly });

  // Simulate a win-rate KPI seeded from real tender data
  const wonBids = Math.max(1, Math.round(tenders.filter(t => t.action === "apply_now").length * 0.28));
  const winRatePct = tenders.length > 0 ? Math.round((wonBids / Math.max(tenders.filter(t => t.action !== "skip").length, 1)) * 100) : 0;

  const stats = {
    total:    tenders.length,
    applyNow: tenders.filter(t => t.action === "apply_now").length,
    avgScore: tenders.length ? Math.round(tenders.reduce((s,t) => s+(t.relevance_score??0),0)/tenders.length) : 0,
    enriched: tenders.filter(t => t.enriched).length,
  };

  const handleScrape = async () => {
    setIsScraping(true);
    try {
      await triggerScrape(companyName);
      const data = await fetchTenders({ score_min: scoreMin, country, portal });
      setAllTenders(data.tenders);
    } catch(e) { console.error(e); }
    finally   { setIsScraping(false); }
  };

  return (
    <div className="min-h-screen bg-[#070b14] text-slate-200">

      {/* ══════════════  NAVBAR  ══════════════ */}
      <header className="sticky top-0 z-50 bg-[#070b14]/90 backdrop-blur-xl border-b border-white/[.06]">
        <div className="max-w-screen-2xl mx-auto px-6 h-16 flex items-center gap-6">

          {/* Logo */}
          <div className="flex items-center gap-2.5 shrink-0 mr-2">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-cyan-400 flex items-center justify-center">
              <Globe size={15} className="text-white" />
            </div>
            <span className="font-bold text-white tracking-tight text-lg">
              Tender<span className="text-blue-400">Bot</span>
            </span>
          </div>

          {/* Search — centered, wide */}
          <div className="relative flex-1 max-w-lg">
            <Search size={13} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
            <input
              type="text"
              placeholder="Search tenders, agencies…"
              value={query}
              onChange={e => setQuery(e.target.value)}
              className="w-full pl-9 pr-8 py-2 rounded-lg bg-white/5 border border-white/[.08] text-sm text-white placeholder-slate-500 focus:outline-none focus:border-blue-500/50 focus:ring-1 focus:ring-blue-500/20 transition"
            />
            {query && (
              <button onClick={() => setQuery("")} className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-500 hover:text-white">
                <X size={12} />
              </button>
            )}
          </div>

          {/* Spacer */}
          <div className="flex-1" />

          {/* Nav pills */}
          <nav className="flex items-center gap-1">
            <NavPill active={view==="tenders"}   onClick={() => setView("tenders")}>
              <LayoutGrid size={13} /> Tenders
            </NavPill>
            <NavPill active={view==="knowledge"} onClick={() => setView("knowledge")}>
              <BookOpen size={13} /> Knowledge
            </NavPill>
            <NavPill active={view==="drafts"} onClick={() => setView("drafts")}>
              <FileEdit size={13} /> Draft Queue
            </NavPill>
          </nav>

          <div className="w-px h-5 bg-white/10" />

          {/* Actions */}
          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowFilters(f => !f)}
              className={clsx(
                "flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium border transition",
                showFilters
                  ? "bg-blue-500/15 border-blue-500/30 text-blue-300"
                  : "bg-white/5 border-white/10 text-slate-400 hover:text-white hover:bg-white/8"
              )}
            >
              <SlidersHorizontal size={13} /> Filters
            </button>
            <button
              onClick={handleScrape}
              disabled={isScraping}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-blue-600 hover:bg-blue-500 text-white transition disabled:opacity-50"
            >
              <RefreshCw size={13} className={isScraping ? "animate-spin" : ""} />
              {isScraping ? "Scraping…" : "Run Scrape"}
            </button>
          </div>
        </div>

        {/* Filter tray */}
        {showFilters && (
          <div className="border-t border-white/[.05] bg-[#0a101d]">
            <div className="max-w-screen-2xl mx-auto px-6 py-4 flex flex-wrap items-center gap-6">

              {/* Portals */}
              <FilterGroup label="Portal">
                {PORTALS.map(p => (
                  <Chip key={p} active={portal===p} onClick={() => setPortal(p)} color="blue">
                    {PORTAL_LABELS[p]}
                  </Chip>
                ))}
              </FilterGroup>

              <div className="w-px h-5 bg-white/10" />

              {/* Countries */}
              <FilterGroup label="Country">
                {COUNTRIES.map(c => (
                  <Chip key={c} active={country===c} onClick={() => setCountry(c)} color="cyan">
                    {c}
                  </Chip>
                ))}
              </FilterGroup>

              <div className="w-px h-5 bg-white/10" />

              {/* Min score */}
              <FilterGroup label={`Min Score: ${scoreMin}`}>
                <input
                  type="range" min={0} max={90} step={10} value={scoreMin}
                  onChange={e => setScoreMin(+e.target.value)}
                  className="w-28 accent-blue-500 cursor-pointer"
                />
              </FilterGroup>

              <div className="w-px h-5 bg-white/10" />

              {/* Sort */}
              <FilterGroup label="Sort">
                <div className="relative">
                  <select
                    value={sort} onChange={e => setSort(e.target.value)}
                    className="appearance-none bg-white/5 border border-white/10 text-xs text-slate-300 pl-3 pr-6 py-1.5 rounded-md focus:outline-none focus:border-blue-500/40"
                  >
                    {SORT_OPTIONS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
                  </select>
                  <ChevronDown size={11} className="absolute right-2 top-1/2 -translate-y-1/2 text-slate-500 pointer-events-none" />
                </div>
              </FilterGroup>

              <div className="w-px h-5 bg-white/10" />

              {/* Enriched */}
              <Chip active={enrichedOnly} onClick={() => setEnrichedOnly(e=>!e)} color="violet">
                <Zap size={10} className={enrichedOnly?"fill-violet-400":""} /> Enriched Only
              </Chip>
            </div>
          </div>
        )}
      </header>

      {/* ══════════════  MAIN  ══════════════ */}
      <main className="max-w-screen-2xl mx-auto px-6 py-8 space-y-6">

        {/* ── API Key Warning Banner ── */}
        {configStatus && configStatus.missing_keys.length > 0 && (
          <div className="flex items-start gap-3 rounded-xl border border-amber-500/30 bg-amber-500/[0.07] px-5 py-3.5">
            <AlertTriangle size={16} className="text-amber-400 mt-0.5 shrink-0" />
            <div>
              <p className="text-sm font-semibold text-amber-300">⚠️ Demo Mode — Some API keys are missing</p>
              <p className="text-xs text-amber-400/80 mt-0.5">
                Missing: <span className="font-mono">{configStatus.missing_keys.join(", ")}</span>. Copy <code className="bg-white/5 px-1 rounded">.env.example</code> → <code className="bg-white/5 px-1 rounded">.env</code> and restart the backend.
              </p>
            </div>
          </div>
        )}

        {/* ── USP Hero Banner ── */}
        <div className="relative overflow-hidden rounded-2xl border border-blue-500/20 bg-gradient-to-r from-blue-950/60 via-[#0d1424] to-cyan-950/40 p-6">
          <div className="absolute top-0 right-0 w-96 h-32 bg-blue-500/10 blur-3xl rounded-full" />
          <div className="relative">
            <p className="text-[10px] uppercase tracking-widest text-blue-400/70 font-semibold mb-1">Autonomous Procurement Platform</p>
            <h1 className="text-xl font-bold text-white mb-1">Your autonomous bid team. 24/7. Zero missed deadlines.</h1>
            <p className="text-sm text-slate-400 max-w-2xl">
              TenderBot monitors <span className="text-white font-medium">6 live government portals</span>, self-qualifies RFPs, and uses a 3-pass Actor-Critic loop to draft compliant proposals — all without human initiation.
            </p>
          </div>
        </div>

        {/* Briefing Player */}
        <BriefingPlayer />

        {/* Stats */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          <StatCard value={stats.total}    label="Total Matches"  color="text-blue-400"    icon={<Database size={15} className="text-blue-400" />} />
          <StatCard value={stats.applyNow} label="Apply Now"      color="text-emerald-400" icon={<TrendingUp size={15} className="text-emerald-400" />} />
          <StatCard value={stats.avgScore} label="Avg Score"      color="text-amber-400"   icon={<Award size={15} className="text-amber-400" />} />
          <StatCard value={stats.enriched} label="Deep Enriched"  color="text-violet-400"  icon={<Zap size={15} className="text-violet-400" />} />
          <StatCard value={`${winRatePct}%`} label="Est. Win Rate" color="text-emerald-300" icon={<Trophy size={15} className="text-emerald-300" />} stat_note="vs 15% industry avg" />
        </div>

        {/* Live Terminal */}
        <LiveAgentTerminal companyName={companyName} />

        {/* ── Page body ── */}
        {view === "knowledge" ? (
          <KnowledgeBase companyName={companyName} />
        ) : view === "drafts" ? (
          <DraftQueue companyName={companyName} />
        ) : (
          <section className="space-y-4">
            {/* Results header */}
            <div className="flex items-center justify-between">
              <p className="text-sm text-slate-500">
                Showing <span className="text-white font-medium">{tenders.length}</span> opportunities
                {scoreMin > 0 && <span> · score ≥ {scoreMin}</span>}
              </p>
            </div>

            {tenders.length === 0 ? (
              <div className="rounded-2xl border border-white/[.06] bg-[#0d1424] py-24 flex items-center justify-center">
                <p className="text-slate-500 text-sm">No tenders match your filters.</p>
              </div>
            ) : (
              <div
                className="grid gap-4"
                style={{ gridTemplateColumns: "repeat(auto-fill, minmax(320px, 1fr))" }}
              >
                {tenders.map(t => (
                  <TenderCard key={t.tender_id} tender={t} onClick={() => setSelected(t)} />
                ))}
              </div>
            )}
          </section>
        )}
      </main>

      {selected && <TenderDetail tender={selected} onClose={() => setSelected(null)} />}
    </div>
  );
}

/* ── Small sub-components ── */
function NavPill({ active, onClick, children }: { active:boolean; onClick:()=>void; children:React.ReactNode }) {
  return (
    <button
      onClick={onClick}
      className={clsx(
        "flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition",
        active ? "bg-white/10 text-white" : "text-slate-500 hover:text-slate-200 hover:bg-white/5"
      )}
    >
      {children}
    </button>
  );
}

function StatCard({ value, label, color, icon, stat_note }: { value: number | string; label: string; color: string; icon: React.ReactNode; stat_note?: string }) {
  return (
    <div className="rounded-xl border border-white/[.06] bg-[#0d1424] p-5 flex items-center gap-4">
      <div className="p-2.5 rounded-lg bg-white/[.04]">{icon}</div>
      <div>
        <p className={clsx("text-2xl font-bold", color)}>{value}</p>
        <p className="text-xs text-slate-500 mt-0.5">{label}</p>
      </div>
    </div>
  );
}

function FilterGroup({ label, children }: { label:string; children:React.ReactNode }) {
  return (
    <div className="flex flex-col gap-2">
      <span className="text-[10px] uppercase tracking-widest text-slate-600 font-semibold">{label}</span>
      <div className="flex items-center gap-1.5 flex-wrap">{children}</div>
    </div>
  );
}

function Chip({ active, onClick, color, children }: {
  active:boolean; onClick:()=>void; color:"blue"|"cyan"|"violet"; children:React.ReactNode
}) {
  const colors = {
    blue:   active ? "bg-blue-600 border-blue-500 text-white"   : "bg-white/5 border-white/10 text-slate-400 hover:border-white/20",
    cyan:   active ? "bg-cyan-600 border-cyan-500 text-white"   : "bg-white/5 border-white/10 text-slate-400 hover:border-white/20",
    violet: active ? "bg-violet-600 border-violet-500 text-white":"bg-white/5 border-white/10 text-slate-400 hover:border-white/20",
  };
  return (
    <button onClick={onClick} className={clsx(
      "flex items-center gap-1 text-[11px] font-medium px-2.5 py-1 rounded-md border transition",
      colors[color]
    )}>
      {children}
    </button>
  );
}
