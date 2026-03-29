"use client";

import { useState, useEffect } from "react";
import { fetchAutoDrafts, approveAutoDraft, BASE_URL } from "@/lib/api";
import { CheckCircle, XCircle, FileText, AlertTriangle, Clock, TrendingUp } from "lucide-react";
import { clsx } from "clsx";

export default function DraftQueue({ companyName }: { companyName: string }) {
  const [drafts, setDrafts] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const loadDrafts = () => {
    fetchAutoDrafts(companyName).then(data => {
      setDrafts(data.drafts || []);
      setLoading(false);
    });
  };

  useEffect(() => {
    loadDrafts();
    
    // Tier 2: Real-time WebSockets
    const wsUrl = BASE_URL.replace("http://", "ws://").replace("https://", "wss://") + "/ws";
    const ws = new WebSocket(wsUrl);
    
    ws.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        if (payload.type === "DRAFT_QUEUED" || payload.type === "DRAFT_STATE_CHANGED") {
          console.log("WebSocket event received, refetching drafts:", payload);
          loadDrafts();
        }
      } catch (e) {
        console.error("Failed to parse WS message", e);
      }
    };
    
    return () => {
      ws.close();
    }
  }, [companyName]);

  const handleAction = async (tenderId: string, action: string) => {
    try {
      await approveAutoDraft(tenderId, companyName, action);
      // Remove or update the local state
      setDrafts(drafts.filter(d => d.tender_id !== tenderId));
    } catch (e) {
      console.error(e);
      alert("Failed to process draft action.");
    }
  };

  if (loading) return <div className="text-slate-500 py-12 text-center">Loading auto-drafts...</div>;

  if (drafts.length === 0) {
    return (
      <div className="rounded-2xl border border-white/[.06] bg-[#0d1424] py-24 flex items-center justify-center">
        <p className="text-slate-500 text-sm">No drafts pending approval. The auto-drafter will queue high-scoring tenders here.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-white flex items-center gap-2">
          <FileText className="text-blue-400" /> Draft Approval Queue
        </h2>
        <span className="bg-amber-500/10 text-amber-400 px-3 py-1 text-xs font-semibold rounded-full border border-amber-500/20">
          {drafts.length} Pending
        </span>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        {drafts.map(d => (
          <div key={d.tender_id} className="rounded-xl border border-white/[.06] bg-[#0d1424] flex flex-col overflow-hidden">
            <div className="p-5 flex-1">
              <div className="flex justify-between items-start mb-2">
                <p className="text-xs text-slate-500 font-mono">{d.tender_id}</p>
                <div className="flex gap-2">
                  {d.trigger_reason === "amendment" && (
                    <span className="flex items-center gap-1 text-[10px] uppercase font-bold text-amber-500 bg-amber-500/10 px-2 py-0.5 rounded border border-amber-500/20">
                      <AlertTriangle size={10} /> Amended
                    </span>
                  )}
                  {d.status === "blocked_waiting_human" && (
                    <span className="flex items-center gap-1 text-[10px] uppercase font-bold text-red-400 bg-red-400/10 px-2 py-0.5 rounded border border-red-400/20">
                      🛑 Blocked: HITL Clarification
                    </span>
                  )}
                </div>
              </div>
              <h3 className="text-sm font-bold text-white mb-2">{d.title}</h3>
              <p className="text-xs text-slate-400 mb-4 line-clamp-3 leading-relaxed opacity-80">{d.draft_markdown.substring(0, 200)}...</p>
              
              <div className="flex items-center gap-4 text-xs text-slate-500">
                <span className="flex items-center gap-1"><TrendingUp size={12} className="text-blue-400" /> Score: {d.score}</span>
                <span className="flex items-center gap-1"><Clock size={12} /> Queued: {new Date(d.queued_at).toLocaleDateString()}</span>
              </div>
            </div>

            <div className="border-t border-white/[.06] bg-slate-900/50 p-3 flex gap-2">
              {d.status === "blocked_waiting_human" ? (
                <>
                  <button 
                    onClick={() => handleAction(d.tender_id, "reject")}
                    className="flex flex-1 items-center justify-center gap-1.5 py-2 rounded-lg text-xs font-medium border border-red-500/20 text-red-400 hover:bg-red-500/10 transition"
                  >
                    <XCircle size={14} /> Abort Bid
                  </button>
                  <button 
                    onClick={() => handleAction(d.tender_id, "waiver")}
                    className="flex flex-1 items-center justify-center gap-1.5 py-2 rounded-lg text-xs font-bold bg-blue-600/90 text-white hover:bg-blue-500 transition shadow-[0_0_15px_rgba(37,99,235,0.3)]"
                  >
                    <CheckCircle size={14} /> Draft Exemption Waiver
                  </button>
                </>
              ) : (
                <>
                  <button 
                    onClick={() => handleAction(d.tender_id, "reject")}
                    className="flex flex-1 items-center justify-center gap-1.5 py-2 rounded-lg text-xs font-medium border border-white/5 text-slate-400 hover:text-white hover:bg-white/5 transition"
                  >
                    <XCircle size={14} /> Reject
                  </button>
                  <button 
                    onClick={() => handleAction(d.tender_id, "revision")}
                    className="flex flex-1 items-center justify-center gap-1.5 py-2 rounded-lg text-xs font-medium bg-amber-500/10 text-amber-400 hover:bg-amber-500/20 transition"
                  >
                    <AlertTriangle size={14} /> Revise
                  </button>
                  <button 
                    onClick={() => handleAction(d.tender_id, "approve")}
                    className="flex flex-1 items-center justify-center gap-1.5 py-2 rounded-lg text-xs font-bold bg-emerald-600/90 text-white hover:bg-emerald-500 transition shadow-[0_0_15px_rgba(16,185,129,0.3)]"
                  >
                    <CheckCircle size={14} /> Approve
                  </button>
                </>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
