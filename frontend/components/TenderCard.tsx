"use client";
import { Tender } from "@/lib/api";
import { clsx } from "clsx";
import { Clock, TrendingUp, Shield, Zap, ChevronRight, AlertCircle } from "lucide-react";

/* ─── tiny helpers ─── */
const fmt = (v?: number | null) =>
  v ? `$${v >= 1_000_000 ? (v / 1_000_000).toFixed(1) + "M" : (v / 1000).toFixed(0) + "K"}` : null;

const PORTAL_COLORS: Record<string, { dot: string; label: string }> = {
  sam_gov:       { dot: "bg-blue-400",   label: "SAM.gov" },
  ted_eu:        { dot: "bg-violet-400", label: "TED EU" },
  ungm:          { dot: "bg-emerald-400",label: "UNGM" },
  find_a_tender: { dot: "bg-amber-400",  label: "Find a Tender" },
  austender:     { dot: "bg-orange-400", label: "AusTender" },
  canadabuys:    { dot: "bg-pink-400",   label: "CanadaBuys" },
};

const FLAGS: Record<string, string> = {
  US:"🇺🇸", UK:"🇬🇧", EU:"🇪🇺", CA:"🇨🇦", AU:"🇦🇺", UN:"🇺🇳",
};

function ScoreArc({ score }: { score: number }) {
  const r = 20, circ = 2 * Math.PI * r;
  const fill = score >= 80 ? "#10b981" : score >= 60 ? "#f59e0b" : "#f43f5e";
  return (
    <svg width="52" height="52" viewBox="0 0 52 52" className="shrink-0 -rotate-90">
      <circle cx="26" cy="26" r={r} fill="none" stroke="rgba(255,255,255,.06)" strokeWidth="4" />
      <circle
        cx="26" cy="26" r={r} fill="none" stroke={fill} strokeWidth="4"
        strokeDasharray={`${(score / 100) * circ} ${circ}`}
        strokeLinecap="round"
        style={{ transition: "stroke-dasharray .6s ease" }}
      />
      <text x="26" y="26" textAnchor="middle" dominantBaseline="central"
        style={{ fontSize: 13, fontWeight: 700, fill: "#fff", transform: "rotate(90deg)", transformOrigin: "26px 26px" }}>
        {score}
      </text>
    </svg>
  );
}

export default function TenderCard({ tender, onClick }: { tender: Tender; onClick: () => void }) {
  const portal = PORTAL_COLORS[tender.source_portal] ?? { dot: "bg-slate-400", label: tender.source_portal };
  const value  = fmt(tender.estimated_value);
  const urgent = (tender.days_until_deadline ?? 999) <= 14;
  const soon   = (tender.days_until_deadline ?? 999) <= 30 && !urgent;
  const isApply = tender.action === "apply_now";

  return (
    <article
      onClick={onClick}
      className={clsx(
        /* base */
        "group relative flex flex-col gap-5 rounded-2xl cursor-pointer",
        "bg-[#0d1424] border transition-all duration-200 overflow-hidden p-5",
        /* hover */
        "hover:bg-[#111827] hover:-translate-y-0.5 hover:shadow-lg hover:shadow-black/40",
        /* apply ring */
        isApply ? "border-emerald-500/25 hover:border-emerald-400/40" : "border-white/[.06] hover:border-white/[.10]",
      )}
    >
      {/* ── Row 1: Source badge + flag + score ── */}
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-2 min-w-0">
          <span className={clsx("inline-block w-2 h-2 rounded-full shrink-0", portal.dot)} />
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider truncate">
            {portal.label}
          </span>
          <span className="text-sm leading-none ml-1" title={tender.country}>
            {FLAGS[tender.country] ?? "🌐"}
          </span>
        </div>
        <ScoreArc score={tender.relevance_score ?? 0} />
      </div>

      {/* ── Row 2: Title & Agency ── */}
      <div className="flex flex-col gap-1 min-w-0">
        <h3 className="text-sm font-semibold text-slate-100 leading-snug line-clamp-2 group-hover:text-blue-300 transition-colors">
          {tender.title}
        </h3>
        <p className="text-xs text-slate-500 truncate">{tender.agency}</p>
      </div>

      {/* ── Row 3: Key Stats ── */}
      <div className="grid grid-cols-3 gap-2 text-xs">
        {value && (
          <div className="flex flex-col gap-0.5">
            <span className="text-slate-500 font-medium">Value</span>
            <span className="text-slate-200 font-semibold">{value}</span>
          </div>
        )}
        {tender.our_probability != null && (
          <div className="flex flex-col gap-0.5">
            <span className="text-slate-500 font-medium">Win&nbsp;Prob</span>
            <span className="text-emerald-400 font-semibold">{tender.our_probability}%</span>
          </div>
        )}
        {tender.eligibility_score != null && (
          <div className="flex flex-col gap-0.5">
            <span className="text-slate-500 font-medium">Eligibility</span>
            <span className="text-violet-400 font-semibold">{tender.eligibility_score}/100</span>
          </div>
        )}
      </div>

      {/* ── Row 4: Description ── */}
      {tender.description && (
        <p className="text-[12px] text-slate-500 leading-relaxed line-clamp-2">
          {tender.description}
        </p>
      )}

      {/* ── Footer: Deadline + action chips ── */}
      <div className="flex items-center justify-between gap-2 pt-1 border-t border-white/[.04] mt-auto">
        <div className="flex items-center gap-2 flex-wrap">
          {/* Deadline */}
          {tender.days_until_deadline != null && (
            <span className={clsx(
              "flex items-center gap-1 text-[11px] font-medium px-2 py-0.5 rounded-md border",
              urgent ? "bg-red-500/10 text-red-400 border-red-500/20"
                : soon ? "bg-amber-500/10 text-amber-400 border-amber-500/20"
                : "bg-white/5 text-slate-400 border-white/10"
            )}>
              {urgent && <AlertCircle size={10} />}
              {!urgent && <Clock size={10} />}
              {tender.days_until_deadline}d left
            </span>
          )}

          {/* Enriched */}
          {tender.enriched && (
            <span className="flex items-center gap-1 text-[11px] font-medium px-2 py-0.5 rounded-md border bg-blue-500/10 text-blue-400 border-blue-500/20">
              <Zap size={9} className="fill-blue-400/30" />Enriched
            </span>
          )}

          {/* Action */}
          {isApply && (
            <span className="flex items-center gap-1 text-[11px] font-semibold px-2 py-0.5 rounded-md border bg-emerald-500/10 text-emerald-400 border-emerald-500/20">
              Apply Now
            </span>
          )}
          {tender.action === "watch" && (
            <span className="text-[11px] font-medium px-2 py-0.5 rounded-md border bg-sky-500/10 text-sky-400 border-sky-500/20">
              Watch
            </span>
          )}
        </div>
        <ChevronRight size={14} className="text-slate-600 group-hover:text-slate-400 shrink-0 transition-colors" />
      </div>
    </article>
  );
}
