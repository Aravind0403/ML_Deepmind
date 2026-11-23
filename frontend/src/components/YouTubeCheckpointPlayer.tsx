"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { Play, Pause, FastForward, CheckCircle2, Youtube, Terminal } from "lucide-react";

export interface VideoCheckpoint {
  at_sec: number;
  kind: string;
  item_id?: string;
  prompt?: string;
  question?: string;
  expected_points?: string[];
}

export interface VideoConfig {
  id: string;
  title: string;
  creator: string;
  youtube_id: string;
  duration_sec: number;
  checkpoints: VideoCheckpoint[];
}

declare global {
  interface Window {
    YT?: any;
    onYouTubeIframeAPIReady?: () => void;
  }
}

function fmtSec(sec: number): string {
  const m = Math.floor(sec / 60);
  const s = Math.floor(sec % 60);
  return `${m}:${s.toString().padStart(2, "0")}`;
}

export function YouTubeCheckpointPlayer({ video }: { video: VideoConfig }) {
  const containerId = `yt-player-${video.id}`;
  const playerRef = useRef<any>(null);
  const [simMode, setSimMode] = useState(false);
  const [currentSec, setCurrentSec] = useState(0);
  const [simPlaying, setSimPlaying] = useState(false);
  const [activeCheckpoint, setActiveCheckpoint] = useState<VideoCheckpoint | null>(null);
  const [cleared, setCleared] = useState<Record<number, boolean>>({});
  const [quickAnswer, setQuickAnswer] = useState("");
  const [quickFeedback, setQuickFeedback] = useState<string | null>(null);

  // Load YouTube IFrame Player API (no Data API key required)
  useEffect(() => {
    if (simMode) return;
    let pollTimer: ReturnType<typeof setInterval> | null = null;
    let mounted = true;

    const initPlayer = () => {
      if (!mounted || !window.YT?.Player) return;
      if (playerRef.current) {
        try {
          playerRef.current.destroy();
        } catch {}
      }
      playerRef.current = new window.YT.Player(containerId, {
        videoId: video.youtube_id,
        playerVars: { rel: 0, modestbranding: 1 },
        events: {
          onStateChange: (event: any) => {
            // YT.PlayerState.PLAYING === 1
            if (event.data === 1) {
              if (pollTimer) clearInterval(pollTimer);
              pollTimer = setInterval(() => {
                if (!playerRef.current?.getCurrentTime) return;
                const t = Math.floor(playerRef.current.getCurrentTime());
                setCurrentSec(t);
                for (const cp of video.checkpoints) {
                  if (!cleared[cp.at_sec] && t >= cp.at_sec && t <= cp.at_sec + 3) {
                    playerRef.current.pauseVideo();
                    setActiveCheckpoint(cp);
                    break;
                  }
                }
              }, 500);
            } else if (pollTimer) {
              clearInterval(pollTimer);
              pollTimer = null;
            }
          },
        },
      });
    };

    if (window.YT && window.YT.Player) {
      initPlayer();
    } else {
      const existing = document.querySelector('script[src="https://www.youtube.com/iframe_api"]');
      if (!existing) {
        const tag = document.createElement("script");
        tag.src = "https://www.youtube.com/iframe_api";
        document.body.appendChild(tag);
      }
      const prev = window.onYouTubeIframeAPIReady;
      window.onYouTubeIframeAPIReady = () => {
        prev?.();
        initPlayer();
      };
    }

    return () => {
      mounted = false;
      if (pollTimer) clearInterval(pollTimer);
      try {
        playerRef.current?.destroy();
      } catch {}
    };
  }, [video.youtube_id, simMode, containerId, cleared, video.checkpoints]);

  // Local Simulator clock (lets you test pause checkpoints offline without waiting 40 minutes)
  useEffect(() => {
    if (!simMode || !simPlaying) return;
    const id = setInterval(() => {
      setCurrentSec((prev) => {
        const next = prev + 1;
        for (const cp of video.checkpoints) {
          if (!cleared[cp.at_sec] && next >= cp.at_sec && prev < cp.at_sec) {
            setSimPlaying(false);
            setActiveCheckpoint(cp);
          }
        }
        return Math.min(next, video.duration_sec);
      });
    }, 250);
    return () => clearInterval(id);
  }, [simMode, simPlaying, cleared, video.checkpoints, video.duration_sec]);

  const jumpToCheckpoint = (cp: VideoCheckpoint) => {
    const preSec = Math.max(0, cp.at_sec - 2);
    setCurrentSec(preSec);
    setActiveCheckpoint(cp);
    setQuickAnswer("");
    setQuickFeedback(null);
    if (!simMode && playerRef.current?.seekTo) {
      playerRef.current.seekTo(cp.at_sec, true);
      playerRef.current.pauseVideo();
    } else {
      setSimPlaying(false);
    }
  };

  const markClearedAndResume = (cp: VideoCheckpoint) => {
    setCleared((prev) => ({ ...prev, [cp.at_sec]: true }));
    setActiveCheckpoint(null);
    setQuickFeedback(null);
    if (!simMode && playerRef.current?.playVideo) {
      playerRef.current.playVideo();
    } else if (simMode) {
      setSimPlaying(true);
    }
  };

  const checkQuickAnswer = (cp: VideoCheckpoint) => {
    const low = quickAnswer.toLowerCase();
    const pts = cp.expected_points || [];
    const hits = pts.filter((p) => low.includes(p.toLowerCase()));
    if (hits.length >= 1 || quickAnswer.trim().length >= 30) {
      setQuickFeedback("Checkpoint verified! Resuming lecture.");
      setTimeout(() => markClearedAndResume(cp), 600);
    } else {
      setQuickFeedback(`Think about: ${pts.join(", ")} — expand your explanation.`);
    }
  };

  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-900/60 p-4 space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <Youtube className="h-5 w-5 text-red-500" />
          <div>
            <h3 className="text-sm font-semibold text-zinc-100">{video.title}</h3>
            <p className="text-xs text-zinc-400">
              {video.creator} · {fmtSec(video.duration_sec)} · {video.checkpoints.length} Pause Checkpoints
            </p>
          </div>
        </div>
        <button
          type="button"
          onClick={() => {
            setSimMode((v) => !v);
            setSimPlaying(false);
          }}
          className="rounded-lg border border-zinc-700 bg-zinc-800 px-3 py-1 font-mono text-xs text-zinc-200 hover:bg-zinc-700"
        >
          {simMode ? "Switch to Live YouTube IFrame" : "Local Checkpoint Simulator"}
        </button>
      </div>

      {!simMode ? (
        <div className="aspect-video w-full overflow-hidden rounded-lg border border-zinc-800 bg-black">
          <div id={containerId} className="h-full w-full" />
        </div>
      ) : (
        <div className="rounded-lg border border-zinc-800 bg-zinc-950 p-4 space-y-3">
          <div className="flex items-center justify-between font-mono text-xs text-zinc-400">
            <span className="flex items-center gap-1.5 text-emerald-400">
              <Terminal className="h-3.5 w-3.5" /> LOCAL CHECKPOINT SIMULATOR (NO NETWORK REQUIRED)
            </span>
            <span>
              {fmtSec(currentSec)} / {fmtSec(video.duration_sec)}
            </span>
          </div>
          <input
            type="range"
            min={0}
            max={video.duration_sec}
            value={currentSec}
            onChange={(e) => setCurrentSec(Number(e.target.value))}
            className="w-full accent-emerald-500"
          />
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => setSimPlaying((p) => !p)}
              className="flex items-center gap-1.5 rounded-md bg-emerald-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-emerald-500"
            >
              {simPlaying ? <Pause className="h-3.5 w-3.5" /> : <Play className="h-3.5 w-3.5" />}
              {simPlaying ? "Pause Sim" : "Play Sim"}
            </button>
            <span className="text-xs text-zinc-500">
              Use the checkpoint buttons below to jump straight to any pause trigger.
            </span>
          </div>
        </div>
      )}

      {/* Checkpoint Timeline Pills */}
      <div className="flex flex-wrap gap-2">
        {video.checkpoints.map((cp) => {
          const isDone = !!cleared[cp.at_sec];
          return (
            <button
              key={cp.at_sec}
              type="button"
              onClick={() => jumpToCheckpoint(cp)}
              className={`flex items-center gap-1.5 rounded-lg border px-3 py-1.5 font-mono text-xs transition-colors ${
                isDone
                  ? "border-emerald-500/40 bg-emerald-500/10 text-emerald-300"
                  : activeCheckpoint?.at_sec === cp.at_sec
                  ? "border-amber-400 bg-amber-500/20 text-amber-200"
                  : "border-zinc-700 bg-zinc-800/80 text-zinc-300 hover:border-zinc-500"
              }`}
            >
              {isDone ? (
                <CheckCircle2 className="h-3.5 w-3.5" />
              ) : (
                <FastForward className="h-3.5 w-3.5" />
              )}
              <span>
                @{fmtSec(cp.at_sec)} · {cp.kind.toUpperCase()}
              </span>
            </button>
          );
        })}
      </div>

      {/* Active Pause Checkpoint Modal Card */}
      {activeCheckpoint && (
        <div className="rounded-lg border border-amber-500/50 bg-amber-500/10 p-4 space-y-3">
          <div className="flex items-center justify-between">
            <span className="font-mono text-xs font-bold uppercase tracking-wider text-amber-300">
              Video Paused @ {fmtSec(activeCheckpoint.at_sec)} — Checkpoint Triggered
            </span>
            <button
              type="button"
              onClick={() => markClearedAndResume(activeCheckpoint)}
              className="text-xs text-zinc-400 underline hover:text-zinc-200"
            >
              Mark Cleared & Resume
            </button>
          </div>
          <p className="text-sm text-zinc-100">
            {activeCheckpoint.prompt || activeCheckpoint.question}
          </p>

          {activeCheckpoint.item_id ? (
            <div className="flex items-center gap-3">
              <Link
                href={`/syllabus/${activeCheckpoint.item_id}`}
                className="rounded-lg bg-amber-500 px-3 py-1.5 text-xs font-semibold text-zinc-950 hover:bg-amber-400"
              >
                Open Graded Exercise ({activeCheckpoint.item_id}) →
              </Link>
              <button
                type="button"
                onClick={() => markClearedAndResume(activeCheckpoint)}
                className="rounded-lg border border-zinc-700 px-3 py-1.5 text-xs text-zinc-300 hover:bg-zinc-800"
              >
                I Solved It — Resume Video
              </button>
            </div>
          ) : (
            <div className="space-y-2">
              <textarea
                rows={2}
                value={quickAnswer}
                onChange={(e) => setQuickAnswer(e.target.value)}
                placeholder="Type your concise conceptual answer to unlock playback..."
                className="w-full rounded-lg border border-zinc-700 bg-zinc-950 p-2 text-sm text-zinc-100"
              />
              <div className="flex items-center gap-3">
                <button
                  type="button"
                  onClick={() => checkQuickAnswer(activeCheckpoint)}
                  className="rounded-lg bg-emerald-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-emerald-500"
                >
                  Verify & Resume
                </button>
                {quickFeedback && <span className="text-xs text-amber-200">{quickFeedback}</span>}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
