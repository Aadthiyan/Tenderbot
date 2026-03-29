"use client";
import { useState, useRef, useEffect } from "react";
import { Play, Pause, Volume2, Calendar } from "lucide-react";
import { VoiceBriefing, fetchLatestBriefing, BASE_URL } from "@/lib/api";
import { clsx } from "clsx";

export default function BriefingPlayer() {
  const [briefing, setBriefing] = useState<VoiceBriefing | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [progress, setProgress] = useState(0);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  useEffect(() => {
    fetchLatestBriefing().then(setBriefing).catch(console.error);
  }, []);

  const togglePlay = () => {
    if (!audioRef.current) return;
    if (isPlaying) {
      audioRef.current.pause();
    } else {
      audioRef.current.play();
    }
    setIsPlaying(!isPlaying);
  };

  const handleTimeUpdate = () => {
    if (audioRef.current) {
      const current = audioRef.current.currentTime;
      const docVal = briefing?.duration_estimate_s || 60;
      // if audio is loaded properly, use .duration, else fallback to estimate
      const total = Number.isSafeInteger(audioRef.current.duration) ? audioRef.current.duration : docVal;
      setProgress((current / total) * 100);
    }
  };

  const handleEnded = () => {
    setIsPlaying(false);
    setProgress(0);
  };

  if (!briefing || !briefing.audio_url) return null;

  // Real audio URL needs pointing to API host if it's served by the backend's /static/ route
  const audioSrc = briefing.audio_url.startsWith("/static/")
    ? `${BASE_URL}${briefing.audio_url}`
    : briefing.audio_url;

  return (
    <div className="relative group overflow-hidden bg-slate-900/50 backdrop-blur-xl border border-slate-700/50 rounded-2xl p-4 shadow-2xl flex items-center gap-4 transition-all hover:bg-slate-800/80 hover:border-blue-500/30">
      
      {/* Hidden Audio Element */}
      <audio
        ref={audioRef}
        src={audioSrc}
        onTimeUpdate={handleTimeUpdate}
        onEnded={handleEnded}
      />

      {/* Play/Pause Button */}
      <button
        onClick={togglePlay}
        className="flex-shrink-0 w-12 h-12 rounded-full bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center text-white shadow-lg shadow-blue-500/20 hover:shadow-blue-500/40 hover:scale-105 transition-all outline-none focus:ring-2 focus:ring-blue-400"
      >
        {isPlaying ? (
          <Pause className="w-5 h-5 fill-current" />
        ) : (
          <Play className="w-5 h-5 fill-current ml-1" />
        )}
      </button>

      {/* Info & Progress */}
      <div className="flex-grow flex flex-col justify-center min-w-0">
        <div className="flex justify-between items-baseline mb-1">
          <h3 className="text-sm font-semibold text-white flex items-center gap-2 truncate">
            <Calendar className="w-3.5 h-3.5 text-blue-400" />
            Daily Intelligence Briefing
          </h3>
          <span className="text-xs text-slate-400 flex items-center gap-1 flex-shrink-0">
            <Volume2 className="w-3.5 h-3.5" />
            {briefing.duration_estimate_s}s
          </span>
        </div>
        
        {/* Progress bar line */}
        <div className="h-1.5 w-full bg-slate-800 rounded-full overflow-hidden mt-1 relative cursor-pointer group-hover:bg-slate-700/80">
          <div 
            className="absolute top-0 left-0 h-full bg-gradient-to-r from-blue-500 to-indigo-400 transition-all duration-200 ease-linear rounded-full"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>
      
      {/* Sound wave decorations */}
      <div className="flex items-center gap-[2px] h-6 px-2 opacity-30 group-hover:opacity-100 transition-opacity">
        <div className={clsx("w-1 bg-blue-400 rounded-full transition-all duration-300", isPlaying ? "h-6 animate-pulse" : "h-2")} />
        <div className={clsx("w-1 bg-blue-400 rounded-full transition-all duration-300", isPlaying ? "h-3 animate-pulse delay-75" : "h-4")} />
        <div className={clsx("w-1 bg-blue-400 rounded-full transition-all duration-300", isPlaying ? "h-5 animate-pulse delay-150" : "h-1.5")} />
        <div className={clsx("w-1 bg-blue-400 rounded-full transition-all duration-300", isPlaying ? "h-2 animate-pulse delay-200" : "h-3")} />
      </div>

    </div>
  );
}
