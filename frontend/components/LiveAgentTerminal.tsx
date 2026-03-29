"use client";
import { useEffect, useState, useRef } from "react";
import { fetchAgentRuns, AgentRun } from "@/lib/api";
import { Terminal, Activity, Server, Database, CheckCircle, XCircle, Loader2 } from "lucide-react";
import clsx from "clsx";

export default function LiveAgentTerminal({ companyName }: { companyName: string }) {
  const [runs, setRuns] = useState<AgentRun[]>([]);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let mounted = true;
    const fetchLogs = async () => {
      try {
        const data = await fetchAgentRuns(companyName);
        if (mounted) {
          // Sort by run_at ascending so newest is at the bottom
          const sorted = data.sort((a, b) => new Date(a.run_at).getTime() - new Date(b.run_at).getTime());
          setRuns(sorted.slice(-50)); // Keep only last 50 for performance
          // Scroll to bottom
          if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
          }
        }
      } catch (err) {
        console.error("Failed to fetch agent runs", err);
      }
    };
    fetchLogs();
    const interval = setInterval(fetchLogs, 4000);
    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, [companyName]);

  return (
    <div className="relative group overflow-hidden bg-[#0a0a0c] border border-green-500/20 rounded-2xl p-4 shadow-2xl flex flex-col h-48 transition-all">
      {/* Terminal Header */}
      <div className="flex items-center justify-between mb-3 border-b border-green-500/20 pb-2">
        <div className="flex items-center gap-2 text-green-400">
          <Terminal size={16} />
          <h3 className="text-xs font-mono font-bold uppercase tracking-wider">Multi-Agent Pipeline Telemetry</h3>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1 text-[10px] text-green-500/70 font-mono">
            <Activity size={10} className="animate-pulse" /> ORCHESTRATOR
          </div>
          <div className="flex items-center gap-1 text-[10px] text-green-500/70 font-mono">
            <Server size={10} className="animate-pulse delay-75" /> LLM_SCORER
          </div>
          <div className="flex items-center gap-1 text-[10px] text-green-500/70 font-mono">
            <Database size={10} className="animate-pulse delay-150" /> RAG_MEMORY
          </div>
        </div>
      </div>

      {/* Terminal Body */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto font-mono text-xs custom-scrollbar pr-2 space-y-2">
        {runs.length === 0 ? (
          <div className="text-green-500/50 italic">Awaiting pipeline initialization...</div>
        ) : (
          runs.map((run) => {
            const time = new Date(run.run_at).toLocaleTimeString("en-US", { hour12: false });
            
            let statusColor = "text-green-400/90";
            let statusIcon = <CheckCircle size={12} className="text-green-500 inline mr-1" />;
            
            if (run.status === "running") {
              statusColor = "text-blue-400";
              statusIcon = <Loader2 size={12} className="text-blue-500 animate-spin inline mr-1" />;
            } else if (run.status === "failed") {
              statusColor = "text-red-400";
              statusIcon = <XCircle size={12} className="text-red-500 inline mr-1" />;
            } else if (run.status === "idle") {
              statusColor = "text-slate-400";
              statusIcon = <span className="inline-block w-2 flex-shrink-0" />;
            }

            return (
              <div key={run._id} className={clsx("flex items-start gap-3 hover:bg-green-500/10 p-1.5 rounded transition-colors break-words", statusColor)}>
                <span className="text-green-600/60 flex-shrink-0">[{time}]</span>
                <span className="font-bold flex-shrink-0 w-28 opacity-80">[{run.agent_name.toUpperCase()}]</span>
                <span className="flex-1 leading-snug">
                  {statusIcon}
                  {run.message}
                </span>
              </div>
            );
          })
        )}
        <div className="animate-pulse text-green-500">_</div>
      </div>
    </div>
  );
}
