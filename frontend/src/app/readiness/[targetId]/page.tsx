"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { Lock, Award, ShieldAlert, CheckCircle2, Swords } from "lucide-react";
import { apiFetch } from "@/lib/api";

export default function ReadinessPage() {
  const params = useParams<{ targetId: string }>();
  const [data, setData] = useState<any>(null);

  const targetId = params?.targetId;

  useEffect(() => {
    if (targetId) {
      apiFetch(`/api/readiness/${targetId}`).then(setData).catch(() => {});
    }
  }, [targetId]);

  if (!data) {
    return <div className="py-12 text-center font-mono text-sm text-zinc-500">Computing Readiness Verdict...</div>;
  }

  if (!data.unlocked) {
    return (
      <div className="mx-auto max-w-xl rounded-2xl border border-zinc-800 bg-zinc-900/70 p-8 text-center space-y-4">
        <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full border border-zinc-700 bg-zinc-950 text-zinc-400">
          <Lock className="h-6 w-6" />
        </div>
        <p className="font-mono text-xs uppercase tracking-widest text-amber-400">
          Pillar 5 · Readiness Score Locked
        </p>
        <h1 className="text-xl font-bold text-white">
          {data.company} — {data.role_title}
        </h1>
        <p className="text-sm text-zinc-400">{data.reason}</p>
        <p className="font-mono text-xs text-zinc-500">
          Current Studio Progress: Stage {data.latest_stage || 0} / 4
        </p>
        <Link
          href={`/studio/${data.target_id}`}
          className="inline-flex items-center gap-2 rounded-lg bg-emerald-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-emerald-500"
        >
          <Swords className="h-4 w-4" /> Complete All 4 Stages in Interview Studio →
        </Link>
      </div>
    );
  }

  const isGo = data.go_no_go.startsWith("GO");

  return (
    <div className="space-y-8">
      <div className="flex flex-wrap items-end justify-between gap-4 border-b border-zinc-800 pb-6">
        <div>
          <p className="font-mono text-xs uppercase tracking-widest text-emerald-400">
            Pillar 5 · Final Verdict (JD vs. CV vs. Prep)
          </p>
          <h1 className="mt-1 text-2xl font-bold text-white sm:text-3xl">
            {data.company} — {data.role_title} ({data.seniority})
          </h1>
        </div>
        <div
          className={`flex items-center gap-2 rounded-xl border px-4 py-2 font-mono text-sm font-bold ${
            isGo
              ? "border-emerald-500 bg-emerald-500/15 text-emerald-300"
              : "border-rose-500 bg-rose-500/15 text-rose-300"
          }`}
        >
          {isGo ? <CheckCircle2 className="h-5 w-5" /> : <ShieldAlert className="h-5 w-5" />}
          <span>{data.go_no_go}</span>
        </div>
      </div>

      {/* Main Verdict KPI Grid */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-4">
        <div className="rounded-xl border border-zinc-800 bg-zinc-900/70 p-5">
          <p className="font-mono text-xs uppercase text-zinc-400">Effective Readiness</p>
          <p className="mt-2 font-mono text-3xl font-bold text-white">
            {data.effective_score}%
          </p>
          <p className="font-mono text-xs text-zinc-400">
            ± {data.confidence_margin}% (n={data.completed_runs} loop{data.completed_runs > 1 ? "s" : ""})
          </p>
        </div>

        <div className="rounded-xl border border-zinc-800 bg-zinc-900/70 p-5">
          <p className="font-mono text-xs uppercase text-zinc-400">The Delta (vs {data.target_bar}% Bar)</p>
          <p
            className={`mt-2 font-mono text-3xl font-bold ${
              data.delta_to_bar >= 0 ? "text-emerald-400" : "text-rose-400"
            }`}
          >
            {data.delta_to_bar >= 0 ? `+${data.delta_to_bar}%` : `${data.delta_to_bar}%`}
          </p>
          <p className="font-mono text-xs text-zinc-400">{data.level_calibration}</p>
        </div>

        <div className="rounded-xl border border-zinc-800 bg-zinc-900/70 p-5">
          <p className="font-mono text-xs uppercase text-zinc-400">Hiring Committee Call</p>
          <p className="mt-2 font-mono text-2xl font-bold text-amber-300">{data.hc_decision}</p>
          <p className="font-mono text-xs text-zinc-400">
            {data.veto_blocked_by ? `VETO: ${data.veto_blocked_by}` : "All Stage Veto Gates Cleared (≥75%)"}
          </p>
        </div>

        <div className="rounded-xl border border-zinc-800 bg-zinc-900/70 p-5 space-y-1.5 font-mono text-xs">
          <p className="uppercase text-zinc-400">3-Axis Decomposition</p>
          <p className="flex justify-between text-zinc-200">
            <span>CV Credibility Fit:</span> <strong>{data.axes.cv_fit}%</strong>
          </p>
          <p className="flex justify-between text-zinc-200">
            <span>JD Syllabus Coverage:</span> <strong>{data.axes.jd_coverage}%</strong>
          </p>
          <p className="flex justify-between text-zinc-200">
            <span>Live Studio Execution:</span> <strong>{data.axes.execution_score}%</strong>
          </p>
        </div>
      </div>

      {/* Per-Stage Hard Floor Veto Gates */}
      <section className="rounded-xl border border-zinc-800 bg-zinc-900/60 p-5 space-y-3">
        <h2 className="text-sm font-bold text-white">
          Per-Stage Hard Floor Veto Gates (Minimum {data.veto_floor}% Required Per Stage)
        </h2>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-4">
          {Object.entries(data.stage_scores).map(([name, sc]: [string, any]) => {
            const ok = sc >= data.veto_floor;
            return (
              <div
                key={name}
                className={`rounded-lg border p-3 ${
                  ok
                    ? "border-emerald-500/40 bg-emerald-500/10"
                    : "border-rose-500/50 bg-rose-500/15"
                }`}
              >
                <p className="font-mono text-[11px] text-zinc-300">{name}</p>
                <p className="mt-1 font-mono text-xl font-bold text-white">{sc}%</p>
                <p className={`font-mono text-[10px] ${ok ? "text-emerald-400" : "text-rose-300"}`}>
                  {ok ? "GATE PASSED" : "VETO TRIGGERED (<75%)"}
                </p>
              </div>
            );
          })}
        </div>
      </section>

      {/* Simulated Hiring Committee Debrief Memo */}
      <section className="rounded-xl border border-zinc-800 bg-zinc-950 p-6 space-y-3">
        <div className="flex items-center gap-2">
          <Award className="h-5 w-5 text-amber-400" />
          <h2 className="text-base font-bold text-white">Simulated Hiring Committee Debrief Memo</h2>
        </div>
        <pre className="whitespace-pre-wrap font-sans text-sm leading-relaxed text-zinc-200">
          {data.hc_memo_markdown}
        </pre>
      </section>
    </div>
  );
}
