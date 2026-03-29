"use client";
import { useState, useEffect, useRef } from "react";
import { Tender, draftProposal, chatWithAgent, recordOutcome, executeAutoSubmit } from "@/lib/api";
import {
  X, ExternalLink, Shield, TrendingUp, Award, CheckCircle,
  XCircle, HelpCircle, ChevronRight, Zap, Clock, Globe,
  AlertTriangle, FileText, Search, Users, PenLine, History,
  ChevronLeft, Loader2, MessageSquare, Send
} from "lucide-react";
import { clsx } from "clsx";

interface Props { tender: Tender; onClose: () => void; }

const TABS = [
  { id: "overview",    label: "Overview",    icon: <Globe size={13} /> },
  { id: "eligibility", label: "Eligibility", icon: <Shield size={13} /> },
  { id: "intel",       label: "Competitor",  icon: <Users size={13} /> },
  { id: "amendments",  label: "Amendments",  icon: <History size={13} /> },
  { id: "chat",        label: "AI Chat",     icon: <MessageSquare size={13} /> },
];

const PORTAL_LABELS: Record<string, string> = {
  sam_gov:"SAM.gov", ted_eu:"TED EU", ungm:"UNGM",
  find_a_tender:"Find-a-Tender UK", austender:"AusTender", canadabuys:"CanadaBuys"
};

const COUNTRY_FLAGS: Record<string, string> = {
  US:"🇺🇸", UK:"🇬🇧", EU:"🇪🇺", CA:"🇨🇦", AU:"🇦🇺", UN:"🇺🇳"
};

function ValueFmt(v: number | null) {
  if (!v) return "TBD";
  return v >= 1_000_000 ? `$${(v / 1_000_000).toFixed(1)}M` : `$${v.toLocaleString()}`;
}

function KpiTile({ label, value, sub, color, icon }: {
  label: string; value: string | number; sub?: string;
  color: string; icon: React.ReactNode
}) {
  return (
    <div className="rounded-xl bg-white/5 border border-white/8 p-4 flex flex-col gap-2">
      <div className={clsx("flex items-center gap-1.5 text-xs font-medium", color)}>
        {icon}<span>{label}</span>
      </div>
      <p className={clsx("text-2xl font-bold", color)}>{value}</p>
      {sub && <p className="text-[11px] text-slate-500">{sub}</p>}
    </div>
  );
}

function StatusIcon({ status }: { status: string }) {
  if (status === "pass") return <CheckCircle size={14} className="text-emerald-400 flex-shrink-0 mt-0.5" />;
  if (status === "fail") return <XCircle size={14} className="text-red-400 flex-shrink-0 mt-0.5" />;
  return <HelpCircle size={14} className="text-yellow-400 flex-shrink-0 mt-0.5" />;
}

// ── Tabs ──────────────────────────────────────────────────────────────────────

function OverviewTab({ tender }: { tender: Tender }) {
  return (
    <div className="space-y-5">
      {/* KPI strip */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <KpiTile label="Relevance" value={`${tender.relevance_score ?? "—"}/100`} color="text-blue-400" icon={<TrendingUp size={13} />} sub="AI match score" />
        <KpiTile label="Eligibility" value={`${tender.eligibility_score ?? "—"}/100`} color="text-violet-400" icon={<Shield size={13} />} sub="Compliance fit" />
        <KpiTile label="Win Probability" value={`${tender.our_probability ?? "—"}%`} color="text-emerald-400" icon={<Award size={13} />} sub="vs competitors" />
        <KpiTile label="SMB Win Rate" value={`${tender.smb_win_rate ?? "—"}%`} color="text-yellow-400" icon={<TrendingUp size={13} />} sub="Market average" />
      </div>

      {/* Core meta */}
      <div className="rounded-xl bg-white/5 border border-white/8 p-4 grid grid-cols-2 gap-x-6 gap-y-3 text-sm">
        {[
          ["Agency", tender.agency],
          ["Country", `${COUNTRY_FLAGS[tender.country] ?? ""} ${tender.country}`],
          ["Portal", PORTAL_LABELS[tender.source_portal] ?? tender.source_portal],
          ["Reference ID", tender.reference_id ?? "—"],
          ["Est. Value", ValueFmt(tender.estimated_value)],
          ["Deadline", tender.days_until_deadline !== null ? `${tender.days_until_deadline} days` : "—"],
          ["Category Code", tender.category_code ?? "—"],
          ["Status", tender.status],
        ].map(([k, v]) => (
          <div key={k}>
            <p className="text-[10px] text-slate-500 uppercase tracking-wider mb-0.5">{k}</p>
            <p className="font-medium text-white text-sm">{v}</p>
          </div>
        ))}
      </div>

      {/* Description */}
      {tender.description && (
        <div>
          <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2 flex items-center gap-1.5">
            <FileText size={12} /> Description
          </h3>
          <p className="text-sm text-slate-300 leading-relaxed">{tender.description}</p>
        </div>
      )}

      {/* Match reasons & disqualifiers side by side */}
      <div className="grid sm:grid-cols-2 gap-4">
        {tender.match_reasons?.length > 0 && (
          <div>
            <h3 className="text-xs font-semibold text-emerald-400 uppercase tracking-wider mb-2 flex items-center gap-1.5">
              <CheckCircle size={12} /> Why it matches
            </h3>
            <ul className="space-y-2">
              {tender.match_reasons.map((r, i) => (
                <li key={i} className="flex items-start gap-2 text-sm text-slate-300 bg-emerald-500/8 border border-emerald-500/15 rounded-lg px-3 py-2">
                  <CheckCircle size={13} className="text-emerald-400 flex-shrink-0 mt-0.5" />{r}
                </li>
              ))}
            </ul>
          </div>
        )}
        {tender.disqualifiers?.length > 0 && (
          <div>
            <h3 className="text-xs font-semibold text-red-400 uppercase tracking-wider mb-2 flex items-center gap-1.5">
              <AlertTriangle size={12} /> Disqualifiers
            </h3>
            <ul className="space-y-2">
              {tender.disqualifiers.map((d, i) => (
                <li key={i} className="flex items-start gap-2 text-sm text-slate-300 bg-red-500/8 border border-red-500/15 rounded-lg px-3 py-2">
                  <XCircle size={13} className="text-red-400 flex-shrink-0 mt-0.5" />{d}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {/* Intel summary panel */}
      {tender.winning_strategy && (
        <div className="rounded-xl bg-blue-500/8 border border-blue-500/20 p-4">
          <h3 className="text-xs font-semibold text-blue-400 uppercase tracking-wider mb-2 flex items-center gap-1.5">
            <Search size={12} /> Winning Strategy
          </h3>
          <p className="text-sm text-slate-300 leading-relaxed">{tender.winning_strategy}</p>
        </div>
      )}
    </div>
  );
}

function EligibilityTab({ tender }: { tender: Tender }) {
  const checklist = tender.eligibility_checklist ?? [];
  const actionPlan = tender.eligibility_action_plan ?? [];
  const reqs = tender.eligibility_requirements ?? [];

  if (!tender.enriched && checklist.length === 0 && reqs.length === 0) {
    return (
      <div className="text-center py-16 text-slate-500">
        <Shield size={36} className="mx-auto mb-3 opacity-20" />
        <p className="font-medium text-slate-400">Eligibility analysis not yet available</p>
        <p className="text-sm mt-1">This tender hasn't been deep-scraped yet (score &lt; 75).</p>
      </div>
    );
  }

  const passes = checklist.filter((c: any) => c.status === "pass").length;
  const total = checklist.length;

  return (
    <div className="space-y-5">
      {/* Summary bar */}
      {total > 0 && (
        <div className="rounded-xl bg-white/5 border border-white/8 p-4">
          <div className="flex justify-between items-center mb-2">
            <span className="text-sm font-semibold text-white">{passes}/{total} requirements pass</span>
            <span className="text-2xl font-bold text-violet-400">{tender.eligibility_score ?? "—"}/100</span>
          </div>
          <div className="h-2 bg-white/10 rounded-full overflow-hidden">
            <div
              className="h-full rounded-full transition-all duration-700"
              style={{
                width: `${total > 0 ? (passes / total) * 100 : 0}%`,
                background: "linear-gradient(90deg, #8b5cf6, #06b6d4)"
              }}
            />
          </div>
        </div>
      )}

      {/* Checklist */}
      {checklist.length > 0 && (
        <div>
          <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">Requirement Checklist</h3>
          <div className="space-y-2">
            {checklist.map((item: any, i: number) => (
              <div key={i} className={clsx(
                "rounded-lg border p-3",
                item.status === "pass" ? "bg-emerald-500/6 border-emerald-500/20" :
                item.status === "fail" ? "bg-red-500/6 border-red-500/20" :
                "bg-yellow-500/6 border-yellow-500/20"
              )}>
                <div className="flex gap-2">
                  <StatusIcon status={item.status} />
                  <div className="flex-1">
                    <p className="text-sm text-slate-200">{item.requirement}</p>
                    {item.gap && (
                      <p className="text-xs text-red-300 mt-1 italic">Gap: {item.gap}</p>
                    )}
                  </div>
                  <span className={clsx(
                    "text-[10px] font-bold uppercase px-2 py-0.5 rounded-full self-start",
                    item.status === "pass" ? "bg-emerald-500/20 text-emerald-300" :
                    item.status === "fail" ? "bg-red-500/20 text-red-300" :
                    "bg-yellow-500/20 text-yellow-300"
                  )}>{item.status}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Raw requirements */}
      {reqs.length > 0 && checklist.length === 0 && (
        <div>
          <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">Extracted Requirements</h3>
          <ul className="space-y-2">
            {reqs.map((r: string, i: number) => (
              <li key={i} className="flex gap-2 text-sm text-slate-300 bg-white/5 border border-white/8 rounded-lg px-3 py-2">
                <ChevronRight size={14} className="text-slate-500 flex-shrink-0 mt-0.5" />{r}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Action plan */}
      {actionPlan.length > 0 && (
        <div className="rounded-xl bg-violet-500/8 border border-violet-500/20 p-4">
          <h3 className="text-xs font-semibold text-violet-400 uppercase tracking-wider mb-3 flex items-center gap-1.5">
            <Zap size={12} /> Action Plan to Close Gaps
          </h3>
          <ol className="space-y-2">
            {actionPlan.map((step: string, i: number) => (
              <li key={i} className="flex gap-3 text-sm text-slate-300">
                <span className="w-5 h-5 rounded-full bg-violet-500/30 text-violet-300 text-xs flex items-center justify-center flex-shrink-0 font-bold">{i + 1}</span>
                {step}
              </li>
            ))}
          </ol>
        </div>
      )}
    </div>
  );
}

function CompetitorTab({ tender }: { tender: Tender }) {
  return (
    <div className="space-y-5">
      {/* Win probability viz */}
      <div className="grid grid-cols-2 gap-3">
        <div className="rounded-xl bg-white/5 border border-white/8 p-4 text-center">
          <p className="text-3xl font-bold text-emerald-400">{tender.our_probability ?? "—"}%</p>
          <p className="text-xs text-slate-500 mt-1">Our Estimated Win Probability</p>
          {tender.our_probability !== null && (
            <div className="mt-3 h-1.5 bg-white/10 rounded-full overflow-hidden">
              <div className="h-full rounded-full bg-emerald-400 transition-all duration-700" style={{ width: `${tender.our_probability}%` }} />
            </div>
          )}
        </div>
        <div className="rounded-xl bg-white/5 border border-white/8 p-4 text-center">
          <p className="text-3xl font-bold text-yellow-400">{tender.smb_win_rate ?? "—"}%</p>
          <p className="text-xs text-slate-500 mt-1">SMB Historical Win Rate</p>
          {tender.smb_win_rate !== null && (
            <div className="mt-3 h-1.5 bg-white/10 rounded-full overflow-hidden">
              <div className="h-full rounded-full bg-yellow-400 transition-all duration-700" style={{ width: `${tender.smb_win_rate}%` }} />
            </div>
          )}
        </div>
      </div>

      {/* Intel summary */}
      {tender.winning_strategy && (
        <div className="rounded-xl bg-blue-500/8 border border-blue-500/20 p-4">
          <h3 className="text-xs font-semibold text-blue-400 uppercase tracking-wider mb-2 flex items-center gap-1.5">
            <TrendingUp size={12} /> Analyst Assessment
          </h3>
          <p className="text-sm text-slate-300 leading-relaxed">{tender.winning_strategy}</p>
        </div>
      )}

      {/* Competitor list */}
      {tender.top_competitors?.length > 0 ? (
        <div>
          <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3 flex items-center gap-1.5">
            <Users size={12} /> Main Competitors / Incumbents
          </h3>
          <div className="space-y-2">
            {tender.top_competitors.map((comp, i) => (
              <div key={i} className="flex items-center gap-3 rounded-lg bg-white/5 border border-white/8 px-4 py-3">
                <div className="w-7 h-7 rounded-full bg-yellow-500/20 flex items-center justify-center text-yellow-400 font-bold text-xs flex-shrink-0">
                  {i + 1}
                </div>
                <p className="text-sm font-medium text-white">{comp}</p>
                <span className="ml-auto text-[10px] text-slate-500">
                  {i === 0 ? "Primary Incumbent" : "Competitor"}
                </span>
              </div>
            ))}
          </div>
        </div>
      ) : (
        <div className="text-center py-12 text-slate-500">
          <Users size={36} className="mx-auto mb-3 opacity-20" />
          <p>No competitor data available yet.</p>
          <p className="text-sm mt-1">Run a deep scrape on this tender to generate intel.</p>
        </div>
      )}
    </div>
  );
}

function AmendmentsTab({ tender }: { tender: Tender }) {
  const history = tender.amendment_history ?? [];

  const MOCK_AMENDMENTS = [
    { date: "2026-03-10", type: "deadline_extension", summary: "Submission deadline extended from April 1 to May 15.", new_deadline: "2026-05-15" },
    { date: "2026-02-28", type: "new_document", summary: "Q&A clarification document issued. 4 new pages added.", new_deadline: null },
  ];
  const amendments = history.length > 0 ? history : MOCK_AMENDMENTS;

  const typeColors: Record<string, string> = {
    deadline_extension: "text-yellow-400 bg-yellow-500/10 border-yellow-500/30",
    new_document: "text-blue-400 bg-blue-500/10 border-blue-500/30",
    scope_change: "text-orange-400 bg-orange-500/10 border-orange-500/30",
    cancellation: "text-red-400 bg-red-500/10 border-red-500/30",
    clarification: "text-cyan-400 bg-cyan-500/10 border-cyan-500/30",
  };

  return (
    <div className="space-y-5">
      <p className="text-sm text-slate-400">
        TenderBot monitors this tender every 12 hours for changes in deadline, documents, scope, or cancellations.
      </p>
      {amendments.length > 0 ? (
        <div className="relative">
          {/* Timeline */}
          <div className="absolute left-4 top-0 bottom-0 w-px bg-white/10" />
          <div className="space-y-4">
            {amendments.map((am: any, i: number) => (
              <div key={i} className="relative flex gap-4 pl-10">
                <div className="absolute left-2 top-3 w-5 h-5 rounded-full bg-white/10 border border-white/20 flex items-center justify-center">
                  <History size={10} className="text-slate-400" />
                </div>
                <div className={clsx(
                  "flex-1 rounded-xl border p-4",
                  typeColors[am.type] ?? "text-slate-400 bg-white/5 border-white/10"
                )}>
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-[10px] font-bold uppercase tracking-wider">
                      {am.type?.replace(/_/g, " ") ?? "Update"}
                    </span>
                    <span className="text-[10px] text-slate-500 font-mono">
                      {new Date(am.date).toLocaleDateString("en-GB")}
                    </span>
                  </div>
                  <p className="text-sm text-slate-200">{am.summary}</p>
                  {am.new_deadline && (
                    <p className="text-xs mt-1 text-yellow-300 flex items-center gap-1">
                      <Clock size={10} /> New deadline: {am.new_deadline}
                    </p>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      ) : (
        <div className="text-center py-12 text-slate-500">
          <History size={36} className="mx-auto mb-3 opacity-20" />
          <p>No amendments detected so far.</p>
        </div>
      )}
    </div>
  );
}

function AutoFillTab({ tender }: { tender: Tender }) {
  const [filling, setFilling] = useState(false);
  const [result, setResult] = useState<null | { fields_filled: string[]; fields_remaining: string[]; completion_pct: number }>(null);
  const [showResult, setShowResult] = useState(false);

  useEffect(() => {
    if (result) {
      setShowResult(true);
    } else {
      setShowResult(false);
    }
  }, [result]);

  const handleFill = async () => {
    setFilling(true);
    setShowResult(false); // Hide result while refilling
    await new Promise(r => setTimeout(r, 2000));
    setResult({
      fields_filled: ["Company Name", "Contact Email", "Address", "Years in Business", "Registration Number"],
      fields_remaining: ["CAGE Code / DUNS", "System-specific Authorization Token"],
      completion_pct: 71.4
    });
    setFilling(false);
  };

  return (
    <div className="space-y-5">
      <p className="text-sm text-slate-400 leading-relaxed">
        TenderBot will navigate to this tender's application form and pre-fill all fields
        matching your company profile — without clicking Submit.
      </p>

      <div className="rounded-xl bg-white/5 border border-white/8 p-4 space-y-2 text-sm">
        <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">Target Application</p>
        <a href={tender.raw_url} target="_blank" rel="noreferrer"
          className="flex items-center gap-2 text-blue-400 hover:text-blue-300 truncate">
          <ExternalLink size={13} />{tender.raw_url}
        </a>
      </div>

      {!result && !filling && (
        <button
          onClick={handleFill}
          className="w-full py-3 rounded-xl bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-500 hover:to-cyan-500 text-white font-semibold text-sm transition-all flex items-center justify-center gap-2"
        >
          <PenLine size={15} /> Launch Auto-Fill Agent
        </button>
      )}

      {filling && (
        <div className="flex items-center justify-center gap-3 py-8 text-slate-400 text-sm">
          <Loader2 size={20} className="animate-spin text-blue-400" />
          <span>TinyFish Agent filling form fields…</span>
        </div>
      )}

      {result && (
        <div className={clsx("space-y-4 transition-opacity duration-500", showResult ? "opacity-100" : "opacity-0")}>
          {/* Progress */}
          <div className="rounded-xl bg-white/5 border border-white/8 p-4">
            <div className="flex justify-between items-center mb-2">
              <span className="text-sm font-semibold text-white">Completion Rate</span>
              <span className="text-2xl font-bold text-emerald-400">{result.completion_pct}%</span>
            </div>
            <div className="h-2 bg-white/10 rounded-full overflow-hidden">
              <div className="h-full rounded-full bg-emerald-400 transition-all duration-700" style={{ width: `${result.completion_pct}%` }} />
            </div>
          </div>

          {/* Filled fields */}
          <div>
            <h3 className="text-xs font-semibold text-emerald-400 uppercase tracking-wider mb-2">✅ Fields Filled</h3>
            <div className="space-y-1">
              {result.fields_filled.map((f, i) => (
                <div key={i} className="flex items-center gap-2 text-sm bg-emerald-500/8 border border-emerald-500/15 rounded-lg px-3 py-1.5 text-slate-200">
                  <CheckCircle size={12} className="text-emerald-400" /> {f}
                </div>
              ))}
            </div>
          </div>

          {/* Remaining */}
          {result.fields_remaining.length > 0 && (
            <div>
              <h3 className="text-xs font-semibold text-yellow-400 uppercase tracking-wider mb-2">⚠️ Needs Manual Input</h3>
              <div className="space-y-1">
                {result.fields_remaining.map((f, i) => (
                  <div key={i} className="flex items-center gap-2 text-sm bg-yellow-500/8 border border-yellow-500/15 rounded-lg px-3 py-1.5 text-slate-300">
                    <HelpCircle size={12} className="text-yellow-400" /> {f}
                  </div>
                ))}
              </div>
            </div>
          )}

          <button
            onClick={handleFill}
            className="w-full py-2.5 rounded-xl border border-white/15 text-sm text-slate-400 hover:text-white hover:border-white/30 transition-colors flex items-center justify-center gap-2"
          >
            <Loader2 size={13} /> Re-run Auto-Fill
          </button>
        </div>
      )}
    </div>
  );
}

// ── Chat Tab ──────────────────────────────────────────────────────────────────

function ChatTab({ tender }: { tender: Tender }) {
  const [messages, setMessages] = useState<{role: "user" | "agent", content: string}[]>([
    { role: "agent", content: "Hi! You can ask me any questions about this tender, our win probability, or strategy based on our private knowledge." }
  ]);
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
  }, [messages, isTyping]);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;
    
    const userMsg = input.trim();
    setInput("");
    setMessages(prev => [...prev, { role: "user", content: userMsg }]);
    setIsTyping(true);

    try {
      const res = await chatWithAgent(tender.tender_id, "Agile Defend IT", userMsg);
      setMessages(prev => [...prev, { role: "agent", content: res.reply }]);
    } catch (err) {
      setMessages(prev => [...prev, { role: "agent", content: "Sorry, I encountered an error connecting to my brain." }]);
    } finally {
      setIsTyping(false);
    }
  };

  return (
    <div className="flex flex-col h-[60vh]">
      <div className="flex-1 overflow-y-auto pr-2 space-y-4 custom-scrollbar" ref={scrollRef}>
        {messages.map((msg, idx) => (
          <div key={idx} className={clsx("flex flex-col max-w-[85%]", msg.role === "user" ? "ml-auto items-end" : "mr-auto items-start")}>
            <div className={clsx(
              "p-3 rounded-2xl text-[13px] leading-relaxed",
              msg.role === "user" ? "bg-blue-600 text-white rounded-br-sm" : "bg-slate-800 text-slate-200 border border-slate-700/50 rounded-bl-sm"
            )}>
              {msg.content}
            </div>
            <span className="text-[10px] text-slate-500 mt-1 px-1">
              {msg.role === "user" ? "You" : "TenderBot Analyst"}
            </span>
          </div>
        ))}
        {isTyping && (
          <div className="mr-auto items-start max-w-[85%] flex flex-col">
            <div className="p-3 bg-slate-800 border border-slate-700/50 rounded-2xl rounded-bl-sm flex items-center gap-1.5 h-[42px]">
              <div className="w-1.5 h-1.5 bg-blue-400 rounded-full animate-bounce [animation-delay:-0.3s]"></div>
              <div className="w-1.5 h-1.5 bg-blue-400 rounded-full animate-bounce [animation-delay:-0.15s]"></div>
              <div className="w-1.5 h-1.5 bg-blue-400 rounded-full animate-bounce"></div>
            </div>
          </div>
        )}
      </div>

      <form onSubmit={handleSend} className="pt-4 mt-2 border-t border-slate-800/50 relative">
        <input
          type="text"
          value={input}
          onChange={e => setInput(e.target.value)}
          placeholder="Ask about this tender..."
          className="w-full bg-slate-900 border border-slate-700/50 rounded-xl py-3 pl-4 pr-12 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-blue-500/50 transition-colors"
        />
        <button
          type="submit"
          disabled={!input.trim() || isTyping}
          className="absolute right-2 top-[22px] p-1.5 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 disabled:hover:bg-blue-600 text-white rounded-lg transition-colors"
        >
          <Send size={15} />
        </button>
      </form>
    </div>
  );
}

// ── Main Panel ────────────────────────────────────────────────────────────────

export default function TenderDetail({ tender, onClose }: Props) {
  const [tab, setTab] = useState("overview");
  const panelRef = useRef<HTMLElement>(null);
  
  const [isDrafting, setIsDrafting] = useState(false);
  const [draftMarkdown, setDraftMarkdown] = useState<string | null>(null);
  const [approvalStatus, setApprovalStatus] = useState<"pending" | "approved" | "revision">("pending");
  const [outcomeStatus, setOutcomeStatus] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);


  // Close on Escape
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => { if (e.key === "Escape") onClose(); };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  const handleDraftProposal = async () => {
    setIsDrafting(true);
    setApprovalStatus("pending");
    try {
      // Hardcoded company name for demo, normally passed down from context/session
      const result = await draftProposal(tender.tender_id, "Agile Defend IT");
      setDraftMarkdown(result.proposal_markdown);
    } catch(e) {
      console.error(e);
      setDraftMarkdown(`# Error\nFailed to draft proposal.`);
    } finally {
      setIsDrafting(false);
    }
  };

  const closeDraftModal = () => {
    setDraftMarkdown(null);
    setApprovalStatus("pending");
  };

  const handleOutcome = async (outcome: string) => {
    try {
      // Hardcoded company name for demo
      await recordOutcome(tender.tender_id, "Agile Defend IT", outcome);
      setOutcomeStatus(outcome);
    } catch (e) {
      console.error(e);
      alert("Failed to record outcome.");
    }
  };

  const handleSubmitAction = async () => {
    setIsSubmitting(true);
    try {
      await executeAutoSubmit(tender.tender_id, "Agile Defend IT");
      alert("Success! Action Agent filled and staged the proposal payload on the target portal.");
      closeDraftModal();
    } catch (e: any) {
      console.error(e);
      alert("Action Agent Failed: " + (e.message || "Unknown error"));
    } finally {
      setIsSubmitting(false);
    }
  };


  const score = tender.relevance_score ?? 0;
  const scoreColor = score >= 80 ? "#10b981" : score >= 60 ? "#f59e0b" : "#ef4444";

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-end">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/65 backdrop-blur-sm" onClick={onClose} />
      
      {/* Draft Modal */}
      {draftMarkdown && (
        <div className="fixed inset-0 z-[60] flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm" onClick={closeDraftModal}>
          <div className="bg-slate-900 border border-slate-700 rounded-2xl w-full max-w-3xl max-h-[85vh] flex flex-col shadow-2xl overflow-hidden animate-slide-in" onClick={e => e.stopPropagation()}>
            {/* Modal header */}
            <div className="p-4 border-b border-slate-800 flex justify-between items-center bg-slate-800/50">
              <h2 className="text-lg font-bold text-white flex items-center gap-2">
                <PenLine className="text-blue-400" size={18} /> Generated Proposal Draft
              </h2>
              <div className="flex items-center gap-3">
                {/* Approval badge */}
                {approvalStatus === "approved" && (
                  <span className="flex items-center gap-1.5 text-xs font-semibold text-emerald-400 bg-emerald-400/10 border border-emerald-400/20 px-3 py-1 rounded-full">
                    <CheckCircle size={13} /> Approved
                  </span>
                )}
                {approvalStatus === "revision" && (
                  <span className="flex items-center gap-1.5 text-xs font-semibold text-amber-400 bg-amber-400/10 border border-amber-400/20 px-3 py-1 rounded-full">
                    <AlertTriangle size={13} /> Needs Revision
                  </span>
                )}
                {approvalStatus === "pending" && (
                  <span className="flex items-center gap-1.5 text-xs font-semibold text-slate-400 bg-white/5 border border-white/10 px-3 py-1 rounded-full">
                    <Clock size={13} /> Awaiting Review
                  </span>
                )}
                <button onClick={closeDraftModal} className="text-slate-400 hover:text-white p-1">
                  <X size={18} />
                </button>
              </div>
            </div>

            {/* Draft content */}
            <div className="p-6 overflow-y-auto prose prose-invert prose-sm max-w-none custom-scrollbar">
              <pre className="whitespace-pre-wrap font-sans text-slate-300 leading-relaxed bg-transparent p-0 m-0 border-none">
                {draftMarkdown}
              </pre>
            </div>

            {/* Approval action footer */}
            <div className="p-4 border-t border-slate-800 bg-slate-800/30 space-y-3">
              {approvalStatus !== "approved" && (
                <div className="flex items-center gap-2 p-3 rounded-lg bg-amber-500/5 border border-amber-500/15 text-xs text-amber-300">
                  <AlertTriangle size={14} className="shrink-0" />
                  Review the draft carefully before approving. Once approved, you can submit it to your bid team.
                </div>
              )}
              <div className="flex gap-2">
                {/* Left: revision/approve buttons */}
                {approvalStatus !== "approved" ? (
                  <>
                    <button
                      onClick={() => setApprovalStatus("revision")}
                      className="flex items-center gap-1.5 px-4 py-2 rounded-xl border border-amber-500/30 text-amber-400 hover:bg-amber-500/10 text-sm font-medium transition-colors"
                    >
                      <XCircle size={15} /> Needs Revision
                    </button>
                    <button
                      onClick={() => setApprovalStatus("approved")}
                      className="flex-1 flex items-center justify-center gap-1.5 px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-sm font-semibold transition-colors"
                    >
                      <CheckCircle size={15} /> Approve Draft
                    </button>
                  </>
                ) : (
                  <>
                    <button
                      onClick={() => setApprovalStatus("pending")}
                      className="flex items-center gap-1.5 px-4 py-2 rounded-xl border border-white/10 text-slate-400 hover:text-white text-sm font-medium transition-colors"
                    >
                      <XCircle size={15} /> Revoke Approval
                    </button>
                    <button
                      onClick={handleSubmitAction}
                      disabled={isSubmitting}
                      className="flex-1 flex items-center justify-center gap-1.5 px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-sm font-semibold transition-colors disabled:opacity-50"
                    >
                      {isSubmitting ? <Loader2 size={15} className="animate-spin" /> : <FileText size={15} />}
                      {isSubmitting ? "Action Agent Running..." : "Submit to Bid Team"}
                    </button>
                  </>
                )}
              </div>
            </div>
          </div>
        </div>
      )}


      {/* Panel */}
      <aside
        ref={panelRef}
        className="relative z-10 h-full w-full max-w-2xl flex flex-col overflow-hidden animate-slide-in"
        style={{ background: "#0d1525", borderLeft: "1px solid rgba(99,179,237,0.12)" }}
        onClick={e => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex-shrink-0 border-b border-white/10 p-4">
          <div className="flex items-start gap-3">
            {/* Score circle */}
            <div className="relative w-12 h-12 flex-shrink-0">
              <svg className="w-12 h-12 -rotate-90" viewBox="0 0 48 48">
                <circle cx="24" cy="24" r="20" fill="none" stroke="rgba(255,255,255,0.07)" strokeWidth="4" />
                <circle cx="24" cy="24" r="20" fill="none" stroke={scoreColor} strokeWidth="4"
                  strokeDasharray={`${(score / 100) * 125.7} 125.7`} strokeLinecap="round" />
              </svg>
              <span className="absolute inset-0 flex items-center justify-center text-[11px] font-bold text-white">{score}</span>
            </div>

            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 text-xs text-slate-500 mb-0.5">
                <span className="text-slate-400">{PORTAL_LABELS[tender.source_portal] ?? tender.source_portal}</span>
                <ChevronRight size={11} />
                <span className="font-mono">{tender.reference_id ?? tender.tender_id.slice(0, 14)}</span>
              </div>
              <h2 className="text-sm font-bold text-white leading-snug line-clamp-2">{tender.title}</h2>
              <p className="text-xs text-slate-400 mt-0.5">
                {COUNTRY_FLAGS[tender.country] ?? ""} {tender.agency}
              </p>
            </div>

            <div className="flex gap-1 flex-shrink-0">
              <a
                href={tender.raw_url}
                target="_blank"
                rel="noopener noreferrer"
                className="p-2 rounded-lg bg-blue-600/20 text-blue-400 hover:bg-blue-600/30 transition-colors"
                title="Open on portal"
              >
                <ExternalLink size={15} />
              </a>
              <button
                onClick={onClose}
                className="p-2 rounded-lg hover:bg-white/10 text-slate-400 hover:text-white transition-colors"
                title="Close (Esc)"
              >
                <X size={15} />
              </button>
            </div>
          </div>

          {/* Tab bar */}
          <div className="flex gap-1 mt-4 overflow-x-auto pb-1 scrollbar-none">
            {TABS.map(t => (
              <button
                key={t.id}
                onClick={() => setTab(t.id)}
                className={clsx(
                  "flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap transition-all",
                  tab === t.id
                    ? "bg-blue-600 text-white"
                    : "text-slate-400 hover:text-white hover:bg-white/8"
                )}
              >
                {t.icon}{t.label}
              </button>
            ))}
          </div>
        </div>

        {/* Tab content */}
        <div className="flex-1 overflow-y-auto p-5" key={tab}>
          <div className="animate-fade-in">
            {tab === "overview" && <OverviewTab tender={tender} />}
            {tab === "eligibility" && <EligibilityTab tender={tender} />}
            {tab === "intel" && <CompetitorTab tender={tender} />}
            {tab === "amendments" && <AmendmentsTab tender={tender} />}
            {tab === "chat" && <ChatTab tender={tender} />}
          </div>
        </div>

        {/* Footer CTA */}
        <div className="flex-shrink-0 border-t border-white/10 p-4 flex gap-2">
          <a
            href={tender.raw_url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center justify-center gap-2 px-6 py-2.5 rounded-xl border border-blue-500/30 text-blue-400 hover:bg-blue-500/10 font-semibold text-sm transition-colors"
          >
            <ExternalLink size={14} /> View Source
          </a>
          <button
            onClick={handleDraftProposal}
            disabled={isDrafting}
            className="flex-1 flex items-center justify-center gap-2 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-semibold text-sm transition-colors disabled:opacity-70"
          >
            {isDrafting ? <Loader2 size={16} className="animate-spin" /> : <PenLine size={16} />} 
            {isDrafting ? "Drafting..." : "One-Click Draft Proposal"}
          </button>
        </div>

        {/* Outcome Feedback Loop (Feature 3) */}
        <div className="flex-shrink-0 border-t border-white/10 p-4 bg-slate-900/50">
          <p className="text-xs text-slate-400 font-semibold uppercase tracking-wider mb-3">Feedback Loop: Log Bid Outcome</p>
          <div className="flex gap-2">
            <button onClick={() => handleOutcome('won')} className="flex-1 py-2 bg-emerald-600/20 text-emerald-400 hover:bg-emerald-600/30 border border-emerald-500/30 rounded-lg text-sm font-medium transition-colors">
              🏆 Won
            </button>
            <button onClick={() => handleOutcome('lost')} className="flex-1 py-2 bg-red-600/20 text-red-400 hover:bg-red-600/30 border border-red-500/30 rounded-lg text-sm font-medium transition-colors">
              ❌ Lost
            </button>
            <button onClick={() => handleOutcome('no_bid')} className="flex-1 py-2 bg-slate-800 text-slate-400 hover:bg-slate-700 border border-slate-600 rounded-lg text-sm font-medium transition-colors">
              🚫 No Bid
            </button>
          </div>
          {outcomeStatus && <p className="text-xs text-emerald-400 mt-3 text-center font-medium font-sans">Outcome successfully recorded: {outcomeStatus.toUpperCase()}</p>}
        </div>
      </aside>
    </div>
  );
}
