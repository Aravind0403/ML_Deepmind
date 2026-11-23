"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { BarChart3, CheckCircle2, AlertTriangle, ArrowRight, Award } from "lucide-react";
import { apiFetch } from "@/lib/api";

const BUCKET_LABELS: Record<string, string> = {
  conceptual_gap: "Conceptual / Math Gap",
  implementation_friction: "Implementation / API Friction",
  complexity_bottleneck_blindness: "Complexity / Hardware Bottleneck Blindness",
  communication_structuring: "Communication / Trade-Off Structuring",
  time_pressure_collapse: "Time-Pressure Collapse",
};

export default function PrepRecapPage() {
  const params = useParams<{ sessionId: string }>();
  const [recap, setRecap] = useState<any>(null);

  const sessionId = params?.sessionId;

  useEffect(() => {
    if (sessionId) {
      apiFetch(`/api/recap/${sessionId}`).then(setRecap).catch(() => {});
    }
  }, [sessionId]);

  if (!recap) {
    return <div className="py-12 text-center font-mono text-sm text-zinc-500">Loading Prep Recap telemetry...</div>;
  }

  return (
    <div className="space-y-8">
      <div className="flex flex-wrap items-end justify-between gap-4 border-b border-zinc-800 pb-6">
        <div>
          <p className="font-mono text-xs uppercase tracking-widest text-amber-400">
            Pillar 4 · Analytics & Diagnostics ({recap.status.toUpperCase()})
          </p>
          <h1 className="mt-1 text-2xl font-bold text-white sm:text-3xl">
            Prep Recap — {recap.company} ({recap.role_title})
          </h1>
          <p className="mt-1 text-sm text-zinc-400">
            Performance telemetry, 5-bucket root-cause failure taxonomy, and targeted remediation links injected directly into your Core Syllabus FSRS queue.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Link
            href={`/studio/${recap.target_id}`}
            className="rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 text-xs font-semibold text-zinc-200 hover:bg-zinc-800"
          >
            Back to Studio
          </Link>
          <Link
            href={`/readiness/${recap.target_id}`}
            className="flex items-center gap-1.5 rounded-lg bg-emerald-600 px-4 py-2 text-xs font-semibold text-white hover:bg-emerald-500"
          >
            <Award className="h-4 w-4" /> Readiness Verdict
          </Link>
        </div>
      </div>

      {/* Strengths Heatmap */}
      <section className="space-y-3">
        <h2 className="flex items-center gap-2 text-base font-bold text-white">
          <BarChart3 className="h-4 w-4 text-emerald-400" /> Strengths & Stage Heatmap
        </h2>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {recap.heatmap.map((cell: any) => {
            const bg =
              cell.score >= 85
                ? "border-emerald-500/50 bg-emerald-500/15"
                : cell.score >= 70
                ? "border-amber-500/40 bg-amber-500/10"
                : cell.score > 0
                ? "border-rose-500/40 bg-rose-500/10"
                : "border-zinc-800 bg-zinc-900/50";
            return (
              <div key={cell.area} className={`rounded-xl border p-4 ${bg}`}>
                <p className="font-mono text-xs text-zinc-300">{cell.area}</p>
                <div className="mt-2 flex items-baseline justify-between">
                  <span className="font-mono text-2xl font-bold text-white">{cell.score}%</span>
                  <span className="font-mono text-[11px] uppercase text-zinc-300">
                    {cell.passed ? "STAFF BAR MET" : cell.score > 0 ? "BELOW BAR" : "NOT REACHED"}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </section>

      {/* 5-Bucket Root-Cause Failure Taxonomy & Session Diff */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="rounded-xl border border-zinc-800 bg-zinc-900/60 p-5 space-y-4">
          <h2 className="text-sm font-bold text-white">5-Bucket Root-Cause Failure Taxonomy</h2>
          <div className="space-y-2.5">
            {Object.entries(recap.failure_taxonomy).map(([k, count]: [string, any]) => (
              <div key={k} className="space-y-1">
                <div className="flex justify-between font-mono text-xs">
                  <span className="text-zinc-300">{BUCKET_LABELS[k] || k}</span>
                  <span className={count > 0 ? "text-rose-400 font-bold" : "text-zinc-500"}>
                    {count} signal{count === 1 ? "" : "s"}
                  </span>
                </div>
                <div className="h-2 w-full rounded-full bg-zinc-800 overflow-hidden">
                  <div
                    className="h-full rounded-full bg-rose-500"
                    style={{ width: `${Math.min(100, count * 25)}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="rounded-xl border border-zinc-800 bg-zinc-900/60 p-5 space-y-4">
          <h2 className="text-sm font-bold text-white">Strengths vs. Vulnerability Report</h2>
          <div className="space-y-3 text-xs">
            <div>
              <p className="font-mono text-[11px] font-bold uppercase text-emerald-400 mb-1">
                Consistent Staff-Level Strengths
              </p>
              {recap.strengths.length === 0 ? (
                <p className="text-zinc-500">No strengths logged yet.</p>
              ) : (
                recap.strengths.map((s: string, i: number) => (
                  <p key={i} className="flex items-start gap-1.5 text-zinc-200 mb-1">
                    <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400 shrink-0 mt-0.5" />
                    <span>{s}</span>
                  </p>
                ))
              )}
            </div>
            <div>
              <p className="font-mono text-[11px] font-bold uppercase text-rose-400 mb-1">
                Identified Vulnerabilities
              </p>
              {recap.vulnerabilities.length === 0 ? (
                <p className="text-emerald-300">Zero critical vulnerabilities flagged in this run.</p>
              ) : (
                recap.vulnerabilities.map((v: string, i: number) => (
                  <p key={i} className="flex items-start gap-1.5 text-rose-200 mb-1">
                    <AlertTriangle className="h-3.5 w-3.5 text-rose-400 shrink-0 mt-0.5" />
                    <span>{v}</span>
                  </p>
                ))
              )}
            </div>
          </div>

          {recap.session_diff && (
            <div className="rounded-lg border border-zinc-800 bg-zinc-950 p-3">
              <p className="font-mono text-[11px] font-bold uppercase text-sky-400 mb-1">
                Delta vs. Previous Attempt ({recap.session_diff.previous_session_id})
              </p>
              <div className="flex flex-wrap gap-3 font-mono text-xs">
                {Object.entries(recap.session_diff.stage_deltas).map(([k, v]: [string, any]) => (
                  <span key={k} className={v >= 0 ? "text-emerald-400" : "text-rose-400"}>
                    {k}: {v >= 0 ? `+${v}%` : `${v}%`}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Targeted Remediation Links */}
      <section className="rounded-xl border border-sky-500/30 bg-sky-500/5 p-5 space-y-3">
        <h2 className="text-sm font-bold text-white">
          Targeted Remediation — Patch Identified Gaps in Core Syllabus
        </h2>
        <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
          {recap.remediation.map((r: any) => (
            <Link
              key={r.item_id}
              href={`/syllabus/${r.item_id}`}
              className="flex items-center justify-between rounded-lg border border-zinc-800 bg-zinc-950 p-3 hover:border-sky-500/60"
            >
              <div>
                <p className="text-sm font-semibold text-white">{r.title}</p>
                <p className="text-xs text-zinc-400">{r.reason}</p>
              </div>
              <ArrowRight className="h-4 w-4 text-sky-400 shrink-0" />
            </Link>
          ))}
        </div>
      </section>
    </div>
  );
}
