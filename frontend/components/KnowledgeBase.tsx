"use client";

import { useState, useEffect } from "react";
import { 
  fetchKnowledge, 
  uploadKnowledgeText, 
  uploadKnowledgeFile, 
  KnowledgeItem,
  fetchProfile,
  saveProfile,
  fetchAuditLogs
} from "@/lib/api";
import { 
  FileText, Upload, Plus, Loader2, CheckCircle2, AlertCircle, Trash2, BookOpen, UserCircle, Shield, Clock, Settings, UploadCloud, MessageSquare
} from "lucide-react";
import { clsx } from "clsx";

interface Props {
  companyName: string;
}

export default function KnowledgeBase({ companyName }: Props) {
  const [items, setItems] = useState<KnowledgeItem[]>([]);
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(false);
  const [fetching, setFetching] = useState(true);
  const [status, setStatus] = useState<{ type: "success" | "error" | "info"; msg: string } | null>(null);
  const [persona, setPersona] = useState("");
  const [savingPersona, setSavingPersona] = useState(false);
  const [profile, setProfile] = useState<any>(null);
  const [auditLogs, setAuditLogs] = useState<any[]>([]);
  const [fetchingAudit, setFetchingAudit] = useState(true);

  useEffect(() => {
    loadKnowledge();
    loadProfile();
    loadAuditLogs();
  }, [companyName]);

  const loadAuditLogs = async () => {
    try {
      setFetchingAudit(true);
      const data = await fetchAuditLogs(companyName);
      setAuditLogs(data);
    } catch(e) {
      console.error(e);
    } finally {
      setFetchingAudit(false);
    }
  };

  const loadProfile = async () => {
    try {
      const p = await fetchProfile(companyName);
      setProfile(p);
      if (p.agent_persona) setPersona(p.agent_persona);
    } catch (e) {
      console.error(e);
    }
  };

  const handleSavePersona = async () => {
    if (!profile) return;
    setSavingPersona(true);
    setStatus(null);
    try {
      const updated = { ...profile, agent_persona: persona };
      await saveProfile(updated);
      setProfile(updated);
      setStatus({ type: "success", msg: "Persona saved successfully!" });
    } catch(e) {
      setStatus({ type: "error", msg: "Failed to save persona." });
    } finally {
      setSavingPersona(false);
    }
  };

  const loadKnowledge = async () => {
    try {
      setFetching(true);
      const data = await fetchKnowledge(companyName);
      setItems(data);
    } catch (e) {
      console.error(e);
    } finally {
      setFetching(false);
    }
  };

  const handleTextSubmit = async () => {
    if (!text.trim()) return;
    setLoading(true);
    setStatus(null);
    try {
      const res = await uploadKnowledgeText(companyName, text);
      setText("");
      if (res?.status === "duplicate") {
        setStatus({ type: "info", msg: res.message ?? "This content is already stored in your knowledge base." });
      } else {
        setStatus({ type: "success", msg: "Knowledge ingested and stored permanently!" });
        loadKnowledge();
      }
    } catch (e) {
      setStatus({ type: "error", msg: "Failed to upload text." });
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setLoading(true);
    setStatus(null);
    try {
      const res = await uploadKnowledgeFile(companyName, file);
      if (res?.status === "duplicate") {
        setStatus({ type: "info", msg: res.message ?? `'${file.name}' is already in your knowledge base.` });
      } else {
        setStatus({ type: "success", msg: `'${file.name}' stored permanently in the knowledge base!` });
        loadKnowledge();
      }
    } catch (e) {
      setStatus({ type: "error", msg: "Failed to upload PDF." });
    } finally {
      setLoading(false);
      // Reset file input so the same file can be re-selected if needed
      e.target.value = "";
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <BookOpen className="text-blue-400" size={20} />
            Exclusive Knowledge Base
          </h2>
          <p className="text-sm text-slate-500">
            Train your private agent by uploading company brochures, past bids, or technical expertise.
          </p>
        </div>
      </div>

      {/* Persona Tuning Section */}
      <div className="bg-slate-900/50 backdrop-blur-md rounded-xl p-6 space-y-4 border border-white/5 shadow-xl">
        <h2 className="text-xl font-bold mb-4 text-slate-100 flex items-center gap-2">
          <Settings className="text-slate-400" />
          Agent Identity
        </h2>
        <label className="block text-xs font-semibold text-slate-400 flex items-center gap-2 uppercase mb-3">
          <UserCircle size={16} className="text-purple-400" />
          Agent Persona Instructions
        </label>
        <textarea
          value={persona}
          onChange={(e) => setPersona(e.target.value)}
          placeholder="E.g., Act as a strict technical evaluator. Always prioritize contracts with ISO 9001 requirements..."
          className="w-full h-20 bg-white/5 border border-white/10 rounded-lg p-3 text-sm text-white focus:outline-none focus:border-purple-500/50 resize-none mb-3"
        />
        <div className="flex justify-end">
          <button
            onClick={handleSavePersona}
            disabled={savingPersona || !profile}
            className="flex items-center gap-2 bg-purple-600 hover:bg-purple-500 px-4 py-2 rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
          >
            {savingPersona ? <Loader2 size={16} className="animate-spin" /> : <CheckCircle2 size={16} />}
            Save Persona
          </button>
        </div>
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        {/* Input Section */}
        <div className="bg-slate-900/50 backdrop-blur-md rounded-xl p-6 space-y-4 border border-white/5 shadow-xl">
          <div>
            <label className="block text-xs font-semibold text-slate-400 uppercase mb-2">Add Text Snippet</label>
            <textarea
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="Paste company expertise, technical specs, or specific win strategies..."
              className="w-full h-32 bg-white/5 border border-white/10 rounded-lg p-3 text-sm text-white focus:outline-none focus:border-blue-500/50 resize-none"
            />
            <button
              onClick={handleTextSubmit}
              disabled={loading || !text.trim()}
              className="mt-2 w-full flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-500 py-2 rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
            >
              {loading ? <Loader2 size={16} className="animate-spin" /> : <Plus size={16} />}
              Ingest Text
            </button>
          </div>

          <div className="relative">
            <div className="absolute inset-0 flex items-center"><div className="w-full border-t border-white/10"></div></div>
            <div className="relative flex justify-center text-xs uppercase"><span className="bg-[#0b101a] px-2 text-slate-600">Or Upload PDF</span></div>
          </div>

          <div>
            <label className="group flex flex-col items-center justify-center w-full h-32 border-2 border-dashed border-white/10 rounded-xl cursor-pointer hover:border-blue-500/50 hover:bg-blue-500/5 transition-all">
              <div className="flex flex-col items-center justify-center pt-5 pb-6">
                <Upload size={24} className="text-slate-500 group-hover:text-blue-400 mb-2" />
                <p className="text-sm text-slate-400">Click to upload RFP, Bid docs, or PDFs</p>
              </div>
              <input type="file" className="hidden" accept=".pdf" onChange={handleFileUpload} disabled={loading} />
            </label>
          </div>

          {status && (
            <div className={clsx(
              "flex items-center gap-2 p-3 rounded-lg text-sm border",
              status.type === "success" ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                : status.type === "info" ? "bg-amber-500/10 text-amber-400 border-amber-500/20"
                : "bg-red-500/10 text-red-400 border-red-500/20"
            )}>
              {status.type === "success" ? <CheckCircle2 size={16} />
                : status.type === "info" ? <AlertCircle size={16} />
                : <AlertCircle size={16} />}
              {status.msg}
            </div>
          )}
        </div>

        {/* List Section */}
        <div className="bg-slate-900/50 backdrop-blur-md rounded-xl p-6 space-y-4 flex flex-col border border-white/5 shadow-xl">
          <label className="block text-xs font-semibold text-slate-400 uppercase mb-3">Trained Knowledge ({items.length})</label>
          <div className="flex-1 overflow-y-auto space-y-3 max-h-[400px] pr-2 custom-scrollbar">
            {fetching ? (
              <div className="flex items-center justify-center py-20"><Loader2 className="animate-spin text-blue-500" /></div>
            ) : items.length === 0 ? (
              <div className="text-center py-20 text-slate-600 italic text-sm">No knowledge ingested yet.</div>
            ) : (
              items.map((item) => (
                <div key={item._id} className="p-3 bg-white/5 border border-white/5 rounded-lg group hover:border-white/10 transition-all">
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex items-start gap-3">
                      <div className="mt-1 p-1 bg-blue-500/10 rounded text-blue-400">
                        {item.metadata?.filename ? <FileText size={14} /> : <Plus size={14} />}
                      </div>
                      <div>
                        <p className="text-sm text-slate-200 line-clamp-3 leading-relaxed">{item.text}</p>
                        <p className="text-[10px] text-slate-500 mt-2 flex items-center gap-2">
                          {item.metadata?.filename && <span className="text-blue-400/70 font-medium">📎 {item.metadata.filename}</span>}
                          <span>{new Date(item.created_at).toLocaleDateString()}</span>
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Audit Logs Section */}
      <div className="bg-slate-900/50 backdrop-blur-md rounded-xl p-6 border border-white/5 shadow-xl">
        <h2 className="text-xl font-bold mb-4 text-slate-100 flex items-center gap-2">
          <UploadCloud className="text-blue-400" />
          Zero-Trust Data Access Audit
        </h2>
        <div className="space-y-3 max-h-[300px] overflow-y-auto pr-2 custom-scrollbar">
          {fetchingAudit ? (
            <div className="flex items-center justify-center py-10"><Loader2 className="animate-spin text-emerald-500" /></div>
          ) : auditLogs.length === 0 ? (
            <div className="text-center py-10 text-slate-600 italic text-sm">No data access events logged yet.</div>
          ) : (
            auditLogs.map((log) => (
              <div key={log._id} className="p-3 bg-white/5 border border-white/5 rounded-lg flex items-start gap-3">
                <Clock size={16} className="text-slate-500 mt-0.5 shrink-0" />
                <div>
                  <p className="text-sm font-medium text-slate-200">AI Scorer Accessed Knowledge</p>
                  <p className="text-xs text-slate-400 mt-1">
                    Evaluated against: <span className="text-blue-300 italic">{log.tender_title}</span>
                  </p>
                  <p className="text-xs text-slate-500 mt-1">
                    {new Date(log.accessed_at).toLocaleString()}
                  </p>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
