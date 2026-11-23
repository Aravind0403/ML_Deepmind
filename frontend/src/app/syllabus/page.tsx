"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import {
  BookOpen,
  Bug,
  CheckCircle2,
  Circle,
  Clock,
  FlaskConical,
  Hammer,
  Lightbulb,
  Code2,
  Sigma,
  Sparkles,
  Youtube,
  RefreshCw,
  Zap,
  Sliders,
} from "lucide-react";
import { apiFetch } from "@/lib/api";
import { YouTubeCheckpointPlayer } from "@/components/YouTubeCheckpointPlayer";

const KIND_META: Record<string, { label: string; icon: any; color: string }> = {
  puzzle: { label: "Puzzle", icon: Lightbulb, color: "text-amber-400 border-amber-500/30 bg-amber-500/10" },
  math: { label: "Math", icon: Sigma, color: "text-sky-400 border-sky-500/30 bg-sky-500/10" },
  problem: { label: "Problem", icon: Code2, color: "text-emerald-400 border-emerald-500/30 bg-emerald-500/10" },
  debugging: { label: "Bug Hunt", icon: Bug, color: "text-orange-400 border-orange-500/30 bg-orange-500/10" },
  lab: { label: "Lab", icon: FlaskConical, color: "text-violet-400 border-violet-500/30 bg-violet-500/10" },
  project: { label: "Project", icon: Hammer, color: "text-rose-400 border-rose-500/30 bg-rose-500/10" },
};

export default function SyllabusPage() {
  const [data, setData] = useState<any>(null);
  const [budget, setBudget] = useState(45);
  const [placementUnit, setPlacementUnit] = useState<any>(null);
  const [placementAns, setPlacementAns] = useState("");
  const [placementRes, setPlacementRes] = useState<any>(null);
  const [activeVideo, setActiveVideo] = useState<any>(null);

  const load = (mins: number) => {
    apiFetch(`/api/syllabus?daily_budget_min=${mins}`).then(setData).catch(() => {});
  };

  useEffect(() => {
    load(budget);
  }, [budget]);

  const submitPlacement = async () => {
    if (!placementUnit) return;
    const res = await apiFetch(`/api/syllabus/placement/${placementUnit.id}`, {
      method: "POST",
      body: JSON.stringify({ answer: placementAns }),
    });
    setPlacementRes(res);
    if (res.passed) load(budget);
  };

  const completeReview = async () => {
    await apiFetch("/api/syllabus/review/complete", { method: "POST" });
    load(budget);
  };

  if (!data) {
    return <div className="py-12 text-center font-mono text-sm text-zinc-500">Loading Deep-Path Syllabus...</div>;
  }

  const { tracks, daily_timebox, review, speed_run_ids, research_practice } = data;

  return (
    <div className="space-y-8">
      <div className="flex flex-wrap items-end justify-between gap-4 border-b border-zinc-800 pb-6">
        <div>
          <p className="font-mono text-xs uppercase tracking-widest text-sky-400">
            Pillar 2 · Standalone Evergreen Mastery Engine
          </p>
          <h1 className="mt-1 text-2xl font-bold text-white sm:text-3xl">
            The Core Syllabus (“The Deep-Path”)
          </h1>
          <p className="mt-1 text-sm text-zinc-400">
            Unified, de-duplicated 5-track taxonomy with Placement Quizzes, Daily Time-Boxed Paths, Embedded YouTube Checkpoints, and 150-XP FSRS Spaced Repetition.
          </p>
        </div>
      </div>

      {/* Top Grid: Daily Time-Boxed Path + 150-XP FSRS Spaced Repetition */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Daily Time-Boxed Path */}
        <div className="rounded-xl border border-zinc-800 bg-zinc-900/60 p-5 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Clock className="h-4 w-4 text-sky-400" />
              <h2 className="text-sm font-semibold text-white">Daily Time-Boxed Path</h2>
            </div>
            <div className="flex items-center gap-1">
              {[30, 45, 60, 90].map((m) => (
                <button
                  key={m}
                  type="button"
                  onClick={() => setBudget(m)}
                  className={`rounded px-2 py-0.5 font-mono text-xs ${
                    budget === m
                      ? "bg-sky-500 text-zinc-950 font-semibold"
                      : "bg-zinc-800 text-zinc-400 hover:text-zinc-200"
                  }`}
                >
                  {m}m
                </button>
              ))}
            </div>
          </div>

          <div className="space-y-2">
            {daily_timebox.items.length === 0 ? (
              <p className="text-xs text-emerald-400">All seeded Core Syllabus items completed!</p>
            ) : (
              daily_timebox.items.map((it: any) => {
                const km = KIND_META[it.kind] || KIND_META.problem;
                return (
                  <Link
                    key={it.id}
                    href={`/syllabus/${it.id}`}
                    className="flex items-center justify-between rounded-lg border border-zinc-800 bg-zinc-950 px-3 py-2.5 hover:border-zinc-700"
                  >
                    <div className="min-w-0">
                      <p className="truncate text-sm font-medium text-zinc-100">{it.title}</p>
                      <p className="text-xs text-zinc-500">
                        {it.track_title} · {it.unit_title}
                      </p>
                    </div>
                    <div className="flex items-center gap-2 shrink-0">
                      <span className={`rounded border px-2 py-0.5 font-mono text-[10px] ${km.color}`}>
                        {km.label}
                      </span>
                      <span className="font-mono text-xs text-zinc-400">{it.estimated_minutes}m</span>
                    </div>
                  </Link>
                );
              })
            )}
          </div>
          <p className="font-mono text-[11px] text-zinc-500">
            Planned load: {daily_timebox.planned_minutes}m / {daily_timebox.budget_minutes}m budget
          </p>
        </div>

        {/* 150-XP Spaced Repetition Queue */}
        <div
          id="review"
          className={`rounded-xl border p-5 space-y-4 ${
            review.review_triggered
              ? "border-amber-500/50 bg-amber-500/5"
              : "border-zinc-800 bg-zinc-900/60"
          }`}
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <RefreshCw className="h-4 w-4 text-amber-400" />
              <h2 className="text-sm font-semibold text-white">
                FSRS Spaced Repetition (Every 150 XP)
              </h2>
            </div>
            <span className="font-mono text-xs text-amber-300">
              {review.xp_since_last_review} / {review.review_threshold} XP
            </span>
          </div>

          {review.queue.length === 0 ? (
            <p className="text-xs text-zinc-400">
              Solve Core Syllabus items or run Interview Studio to populate your FSRS memory-decay review queue.
            </p>
          ) : (
            <div className="space-y-2">
              {review.queue.slice(0, 4).map((q: any) => (
                <Link
                  key={q.item_id}
                  href={`/syllabus/${q.item_id}?review=1`}
                  className="flex items-center justify-between rounded-lg border border-zinc-800 bg-zinc-950 px-3 py-2 hover:border-amber-500/40"
                >
                  <div className="min-w-0">
                    <p className="truncate text-sm text-zinc-100">{q.title}</p>
                    <p className="font-mono text-[10px] text-zinc-500">
                      Retrievability: {q.retrievability_pct}% · Stability: {q.stability_days}d
                      {q.studio_boost > 1 ? ` · Studio Weakness ${q.studio_boost}× Boost` : ""}
                    </p>
                  </div>
                  <span className="font-mono text-xs text-amber-400">Review →</span>
                </Link>
              ))}
            </div>
          )}

          {review.review_triggered && (
            <button
              type="button"
              onClick={completeReview}
              className="rounded-lg bg-amber-500 px-3 py-1.5 text-xs font-semibold text-zinc-950 hover:bg-amber-400"
            >
              Mark 150-XP Review Pass Complete
            </button>
          )}
        </div>
      </div>

      {/* Phase 2 Strip: 6-Drill ML Speed-Run + Research Practice + Systems Sandboxes */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <div className="lg:col-span-2 rounded-xl border border-orange-500/30 bg-orange-500/5 p-4 space-y-3">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div className="flex items-center gap-2">
              <Zap className="h-4 w-4 text-orange-400" />
              <h2 className="text-sm font-bold text-white">
                Non-Negotiable 6-Drill ML Coding Speed-Run (20m Timer · 15m Stuck Cutoff)
              </h2>
            </div>
            <Link
              href="/sandboxes"
              className="flex items-center gap-1 rounded border border-emerald-500/40 bg-emerald-500/10 px-2.5 py-1 font-mono text-[11px] text-emerald-300 hover:bg-emerald-500/20"
            >
              <Sliders className="h-3 w-3" /> Open Roofline & nano-vLLM Sandboxes →
            </Link>
          </div>
          <div className="flex flex-wrap gap-2">
            {(speed_run_ids || []).map((sid: string, idx: number) => (
              <Link
                key={sid}
                href={`/syllabus/${sid}?speedrun=1`}
                className="rounded-lg border border-zinc-800 bg-zinc-950 px-2.5 py-1.5 font-mono text-xs text-zinc-200 hover:border-orange-400"
              >
                #{idx + 1} {sid}
              </Link>
            ))}
          </div>
        </div>

        <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-4 space-y-2">
          <h2 className="font-mono text-xs font-bold uppercase text-violet-300">
            Research Practice Referee Protocol
          </h2>
          {(research_practice || []).map((rp: any) => (
            <div key={rp.id} className="text-xs text-zinc-300">
              <strong className="text-zinc-100">{rp.title}:</strong> {rp.prompt}
            </div>
          ))}
        </div>
      </div>

      {/* Active Embedded YouTube Checkpoint Player Drawer */}
      {activeVideo && (
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="font-mono text-xs uppercase text-red-400">Embedded Lecture Player</span>
            <button
              type="button"
              onClick={() => setActiveVideo(null)}
              className="text-xs text-zinc-400 hover:text-zinc-200"
            >
              Close Player ✕
            </button>
          </div>
          <YouTubeCheckpointPlayer video={activeVideo} />
        </div>
      )}

      {/* Unified 5-Track Taxonomy */}
      <div className="space-y-6">
        {tracks.map((tr: any) => (
          <section
            key={tr.id}
            className="rounded-xl border border-zinc-800 bg-zinc-900/40 p-5 space-y-4"
          >
            <div className="flex flex-wrap items-center justify-between gap-2 border-b border-zinc-800 pb-3">
              <div className="flex items-center gap-3">
                <span
                  className="h-3 w-3 rounded-full"
                  style={{ backgroundColor: tr.color }}
                />
                <div>
                  <h2 className="text-lg font-bold text-white">{tr.title}</h2>
                  <p className="text-xs text-zinc-400">{tr.subtitle}</p>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
              {tr.units.map((u: any) => (
                <div
                  key={u.id}
                  className="rounded-xl border border-zinc-800 bg-zinc-950 p-4 space-y-3"
                >
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <h3 className="text-sm font-semibold text-white">{u.title}</h3>
                      <p className="mt-0.5 font-mono text-[11px] text-zinc-500">
                        {u.counts.puzzle} puzzles · {u.counts.math} math · {u.counts.problem} problems · {u.counts.debugging || 0} bug hunts · {u.counts.lab} labs · {u.counts.project} projects
                      </p>
                    </div>
                    <div className="flex items-center gap-2 shrink-0">
                      <button
                        type="button"
                        onClick={() => {
                          setPlacementUnit(u);
                          setPlacementAns("");
                          setPlacementRes(null);
                        }}
                        className="flex items-center gap-1 rounded border border-zinc-700 bg-zinc-900 px-2 py-1 font-mono text-[10px] text-zinc-300 hover:border-sky-500 hover:text-sky-300"
                      >
                        <Sparkles className="h-3 w-3" />
                        Skip (Quiz)
                      </button>
                    </div>
                  </div>

                  {/* Embedded YouTube Lectures attached to this unit */}
                  {u.videos && u.videos.length > 0 && (
                    <div className="flex flex-wrap gap-2">
                      {u.videos.map((v: any) => (
                        <button
                          key={v.id}
                          type="button"
                          onClick={() => setActiveVideo(v)}
                          className="flex items-center gap-1.5 rounded-lg border border-red-500/30 bg-red-500/10 px-2.5 py-1 text-xs text-red-200 hover:bg-red-500/20"
                        >
                          <Youtube className="h-3.5 w-3.5 text-red-400" />
                          <span className="truncate max-w-[260px]">{v.title}</span>
                          <span className="font-mono text-[10px] text-red-300/80">
                            ({v.checkpoints.length} pauses)
                          </span>
                        </button>
                      ))}
                    </div>
                  )}

                  {/* Items List */}
                  <ul className="space-y-1.5">
                    {u.items.map((it: any) => {
                      const km = KIND_META[it.kind] || KIND_META.problem;
                      const Icon = km.icon;
                      return (
                        <li key={it.id}>
                          <Link
                            href={`/syllabus/${it.id}`}
                            className="flex items-center justify-between gap-2 rounded-lg border border-zinc-900 bg-zinc-900/50 px-3 py-2 text-sm hover:border-zinc-700 hover:bg-zinc-900"
                          >
                            <div className="flex items-center gap-2.5 min-w-0">
                              {it.status === "completed" ? (
                                <CheckCircle2 className="h-4 w-4 text-emerald-400 shrink-0" />
                              ) : (
                                <Circle className="h-4 w-4 text-zinc-600 shrink-0" />
                              )}
                              <Icon className="h-3.5 w-3.5 text-zinc-400 shrink-0" />
                              <span className="truncate text-zinc-200">{it.title}</span>
                            </div>
                            <div className="flex items-center gap-2 shrink-0">
                              <span className={`rounded border px-1.5 py-0.5 font-mono text-[10px] ${km.color}`}>
                                {km.label}
                              </span>
                              <span className="font-mono text-[10px] text-zinc-500">
                                +{it.xp} XP
                              </span>
                            </div>
                          </Link>
                        </li>
                      );
                    })}
                  </ul>
                </div>
              ))}
            </div>
          </section>
        ))}
      </div>

      {/* Placement Quiz Modal */}
      {placementUnit && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 p-4">
          <div className="w-full max-w-lg rounded-xl border border-zinc-700 bg-zinc-900 p-6 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-base font-bold text-white">
                Placement Quiz — Skip “{placementUnit.title}”
              </h3>
              <button
                type="button"
                onClick={() => setPlacementUnit(null)}
                className="text-zinc-400 hover:text-white"
              >
                ✕
              </button>
            </div>
            <p className="text-sm text-zinc-300">
              {placementUnit.placement?.prompt || "Explain the core mechanism of this unit."}
            </p>
            <textarea
              rows={4}
              value={placementAns}
              onChange={(e) => setPlacementAns(e.target.value)}
              placeholder="Write a concise, Staff-level explanation covering the key mechanism and trade-offs..."
              className="w-full rounded-lg border border-zinc-700 bg-zinc-950 p-3 text-sm text-zinc-100"
            />
            {placementRes && (
              <div
                className={`rounded-lg border p-3 text-xs ${
                  placementRes.passed
                    ? "border-emerald-500/40 bg-emerald-500/10 text-emerald-200"
                    : "border-rose-500/40 bg-rose-500/10 text-rose-200"
                }`}
              >
                {placementRes.feedback}
              </div>
            )}
            <div className="flex justify-end gap-2">
              <button
                type="button"
                onClick={() => setPlacementUnit(null)}
                className="rounded-lg border border-zinc-700 px-3 py-1.5 text-xs text-zinc-300"
              >
                Close
              </button>
              <button
                type="button"
                onClick={submitPlacement}
                className="rounded-lg bg-sky-500 px-4 py-1.5 text-xs font-semibold text-zinc-950 hover:bg-sky-400"
              >
                Verify & Skip Unit
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
