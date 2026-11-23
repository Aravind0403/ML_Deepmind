"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import {
  Target,
  BookOpen,
  Swords,
  Award,
  Clock,
  AlertTriangle,
  ArrowRight,
  Flame,
  TrendingDown,
  Briefcase,
  DollarSign,
  Sliders,
} from "lucide-react";
import { apiFetch } from "@/lib/api";

const CRM_STAGES = ["Researching", "Applied", "Recruiter", "Tech Loop", "Onsite", "Offer"];

export default function OverviewDashboardPage() {
  const [data, setData] = useState<any>(null);
  const [crm, setCrm] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [editingCrm, setEditingCrm] = useState<any>(null);
  const [dateInput, setDateInput] = useState("");
  const [riskHaircut, setRiskHaircut] = useState(0.5); // Risk adjustment for illiquid startup options

  const loadAll = () => {
    Promise.all([apiFetch("/api/overview"), apiFetch("/api/crm")])
      .then(([ov, c]) => {
        setData(ov);
        setCrm(c);
      })
      .catch((e) => setError(e.message));
  };

  useEffect(() => {
    loadAll();
  }, []);

  const saveCrmRecord = async () => {
    if (!editingCrm) return;
    await apiFetch(`/api/crm/${editingCrm.target_id}`, {
      method: "PUT",
      body: JSON.stringify({
        app_stage: editingCrm.app_stage,
        referral_contact: editingCrm.referral_contact,
        cold_email_draft: editingCrm.cold_email_draft,
        interview_dates: editingCrm.interview_dates,
        offer: editingCrm.offer,
      }),
    });
    setEditingCrm(null);
    loadAll();
  };

  if (error) {
    return (
      <div className="rounded-xl border border-rose-500/40 bg-rose-500/10 p-6 text-sm text-rose-200">
        Cannot reach FastAPI backend at <code>http://localhost:8000</code>: {error}. Start the backend with{" "}
        <code>uvicorn backend.main:app --reload</code>.
      </div>
    );
  }

  if (!data) {
    return <div className="py-12 text-center font-mono text-sm text-zinc-500">Loading Command Center...</div>;
  }

  const { core_summary, tracks, pipelines, review } = data;

  return (
    <div className="space-y-8">
      {/* Header Banner */}
      <div className="flex flex-wrap items-end justify-between gap-4 border-b border-zinc-800 pb-6">
        <div>
          <p className="font-mono text-xs uppercase tracking-widest text-emerald-400">
            Pillar 1 · Command Center
          </p>
          <h1 className="mt-1 text-2xl font-bold tracking-tight text-white sm:text-3xl">
            Overview Dashboard — Mastery & Target Pipelines
          </h1>
          <p className="mt-1 text-sm text-zinc-400">
            Evergreen Core Syllabus progress (with FSRS memory decay) decoupled from your dynamic company-specific Interview Studio pipelines.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Link
            href="/syllabus"
            className="flex items-center gap-2 rounded-lg border border-zinc-700 bg-zinc-900 px-4 py-2 text-sm font-medium text-zinc-100 hover:bg-zinc-800"
          >
            <BookOpen className="h-4 w-4 text-sky-400" />
            Core Syllabus
          </Link>
          <Link
            href="/studio"
            className="flex items-center gap-2 rounded-lg bg-emerald-600 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-500"
          >
            <Swords className="h-4 w-4" />
            Enter Interview Studio
          </Link>
        </div>
      </div>

      {/* 150-XP Spaced Repetition Alert */}
      {review.review_triggered && (
        <div className="flex flex-wrap items-center justify-between gap-4 rounded-xl border border-amber-500/50 bg-amber-500/10 p-4">
          <div className="flex items-center gap-3">
            <AlertTriangle className="h-5 w-5 text-amber-400 shrink-0" />
            <div>
              <p className="text-sm font-semibold text-amber-200">
                150-XP Spaced Repetition Trigger Active ({review.xp_since_last_review} XP earned since last review)
              </p>
              <p className="text-xs text-amber-300/80">
                FSRS queue ready — Studio vulnerabilities are boosted 3× to reinforce weak concepts before decay.
              </p>
            </div>
          </div>
          <Link
            href="/syllabus#review"
            className="rounded-lg bg-amber-500 px-3 py-1.5 text-xs font-semibold text-zinc-950 hover:bg-amber-400"
          >
            Run FSRS Review Queue →
          </Link>
        </div>
      )}

      {/* Top KPI Row */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <div className="rounded-xl border border-zinc-800 bg-zinc-900/60 p-5">
          <p className="font-mono text-xs uppercase text-zinc-400">Core Syllabus Baseline</p>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="font-mono text-3xl font-bold text-white">{core_summary.overall_pct}%</span>
            <span className="font-mono text-xs text-zinc-400">
              ({core_summary.completed}/{core_summary.total} items)
            </span>
          </div>
        </div>
        <div className="rounded-xl border border-zinc-800 bg-zinc-900/60 p-5">
          <p className="font-mono text-xs uppercase text-zinc-400">Active Target Pipelines</p>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="font-mono text-3xl font-bold text-emerald-400">{pipelines.length}</span>
            <span className="font-mono text-xs text-zinc-400">
              ({pipelines.filter((p: any) => p.readiness_unlocked).length} Readiness Unlocked)
            </span>
          </div>
        </div>
        <div className="rounded-xl border border-zinc-800 bg-zinc-900/60 p-5">
          <p className="font-mono text-xs uppercase text-zinc-400">Core XP & FSRS Cycle</p>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="flex items-center gap-1 font-mono text-3xl font-bold text-amber-400">
              <Flame className="h-6 w-6" /> {review.total_core_xp}
            </span>
            <span className="font-mono text-xs text-zinc-400">
              {review.xp_to_next_review} XP to next review
            </span>
          </div>
        </div>
      </div>

      {/* Section A: Foundation & Specialization Tracker */}
      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-white">Foundation & Specialization Tracker</h2>
            <p className="text-xs text-zinc-400">
              Solid bar = Peak Mastery earned · Glowing overlay = FSRS Effective Readiness Today (accounts for memory decay).
            </p>
          </div>
          <Link href="/syllabus" className="font-mono text-xs text-sky-400 hover:underline">
            Explore Unified 5-Track Deep-Path →
          </Link>
        </div>

        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
          {tracks.map((tr: any) => (
            <div
              key={tr.id}
              className="rounded-xl border border-zinc-800 bg-zinc-900/60 p-4 space-y-3"
            >
              <div className="flex items-start justify-between gap-2">
                <div>
                  <h3 className="text-sm font-semibold text-white">{tr.title}</h3>
                  <p className="mt-0.5 text-xs text-zinc-400 line-clamp-2">{tr.subtitle}</p>
                </div>
                <span className="font-mono text-xs text-zinc-300 shrink-0">
                  {tr.completed}/{tr.total}
                </span>
              </div>

              <div className="space-y-1.5">
                <div className="h-2.5 w-full overflow-hidden rounded-full bg-zinc-800 relative">
                  <div
                    className="h-full rounded-full opacity-35 transition-all"
                    style={{ width: `${tr.peak_pct}%`, backgroundColor: tr.color }}
                  />
                  <div
                    className="absolute inset-y-0 left-0 rounded-full transition-all"
                    style={{ width: `${tr.effective_pct}%`, backgroundColor: tr.color }}
                  />
                </div>
                <div className="flex items-center justify-between font-mono text-[11px] text-zinc-400">
                  <span>Peak: {tr.peak_pct}%</span>
                  <span className="flex items-center gap-1 text-zinc-200">
                    <TrendingDown className="h-3 w-3 text-zinc-500" />
                    Effective Today: {tr.effective_pct}%
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Section B: Target Company Pipelines */}
      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-white">Target Company Pipelines</h2>
            <p className="text-xs text-zinc-400">
              Driven exclusively by your performance in the 4-Stage Interview Studio. Complete all 4 stages to unlock the Readiness Verdict.
            </p>
          </div>
          <Link href="/studio" className="font-mono text-xs text-emerald-400 hover:underline">
            + Manage Target JDs & CV →
          </Link>
        </div>

        <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
          {pipelines.map((p: any) => (
            <div
              key={p.id}
              className="flex flex-col justify-between rounded-xl border border-zinc-800 bg-zinc-900/70 p-5 space-y-4"
            >
              <div className="space-y-3">
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <div className="flex items-center gap-2">
                      <Target className="h-4 w-4 text-emerald-400" />
                      <span className="font-mono text-xs font-bold uppercase text-emerald-400">
                        {p.company}
                      </span>
                      <span className="rounded bg-zinc-800 px-1.5 py-0.5 font-mono text-[10px] text-zinc-300">
                        {p.seniority}
                      </span>
                    </div>
                    <h3 className="mt-1 text-base font-semibold text-white">{p.role_title}</h3>
                  </div>
                  <span className="font-mono text-xl font-bold text-white">{p.prepared_pct}%</span>
                </div>

                {/* Readiness Progress Bar */}
                <div className="space-y-1">
                  <div className="h-2.5 w-full overflow-hidden rounded-full bg-zinc-800">
                    <div
                      className={`h-full rounded-full transition-all ${
                        p.prepared_pct >= 85
                          ? "bg-emerald-500"
                          : p.prepared_pct >= 50
                          ? "bg-amber-500"
                          : "bg-sky-500"
                      }`}
                      style={{ width: `${Math.min(100, p.prepared_pct)}%` }}
                    />
                  </div>
                  <div className="flex items-center justify-between font-mono text-[11px]">
                    <span className="text-zinc-400">{p.go_no_go}</span>
                    {p.days_left !== null && (
                      <span className="flex items-center gap-1 text-zinc-300">
                        <Clock className="h-3 w-3 text-zinc-500" />
                        {p.days_left}d left · {p.daily_hours_needed}h/day ({p.pacing_status})
                      </span>
                    )}
                  </div>
                </div>

                {/* Extracted JD Skills */}
                <div className="flex flex-wrap gap-1.5">
                  {(p.parsed_skills || []).slice(0, 6).map((sk: string) => (
                    <span
                      key={sk}
                      className="rounded border border-zinc-800 bg-zinc-950 px-2 py-0.5 font-mono text-[10px] text-zinc-400"
                    >
                      {sk}
                    </span>
                  ))}
                </div>
              </div>

              {/* Pipeline Actions */}
              <div className="flex items-center gap-2 pt-2 border-t border-zinc-800">
                <Link
                  href={`/studio/${p.id}`}
                  className="flex flex-1 items-center justify-center gap-1.5 rounded-lg bg-zinc-800 px-3 py-2 text-xs font-semibold text-white hover:bg-zinc-700"
                >
                  <Swords className="h-3.5 w-3.5 text-emerald-400" />
                  {p.latest_session_id ? `Resume Studio (S${p.latest_session_stage})` : "Launch Gauntlet"}
                </Link>
                <Link
                  href={`/readiness/${p.id}`}
                  className={`flex items-center justify-center gap-1.5 rounded-lg border px-3 py-2 text-xs font-semibold ${
                    p.readiness_unlocked
                      ? "border-emerald-500/50 bg-emerald-500/15 text-emerald-300 hover:bg-emerald-500/25"
                      : "border-zinc-800 bg-zinc-950 text-zinc-500 hover:text-zinc-300"
                  }`}
                >
                  <Award className="h-3.5 w-3.5" />
                  Readiness
                  <ArrowRight className="h-3 w-3" />
                </Link>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Phase 2 Extension: Application Pipeline CRM, Burnout Spacing Guardrail & Offer Comparator */}
      {crm && (
        <section className="space-y-4 border-t border-zinc-800 pt-6">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div className="flex items-center gap-2">
              <Briefcase className="h-4 w-4 text-sky-400" />
              <div>
                <h2 className="text-lg font-semibold text-white">
                  Application Pipeline CRM, Burnout Spacing & RSU/Options Comparator
                </h2>
                <p className="text-xs text-zinc-400">
                  Track application stages, referrals, cold-email outreach, interview spacing (&le;3 loops/week), and risk-adjusted offers.
                </p>
              </div>
            </div>
            <span
              className={`rounded-full border px-3 py-1 font-mono text-xs ${
                crm.burnout_guardrail?.burnout_warning
                  ? "border-rose-500 bg-rose-500/15 text-rose-200 font-bold"
                  : "border-emerald-500/40 bg-emerald-500/10 text-emerald-300"
              }`}
            >
              {crm.burnout_guardrail?.advice}
            </span>
          </div>

          <div className="overflow-x-auto rounded-xl border border-zinc-800 bg-zinc-900/50">
            <table className="w-full text-left font-mono text-xs">
              <thead className="border-b border-zinc-800 bg-zinc-950 text-zinc-400">
                <tr>
                  <th className="px-4 py-3">Company / Role</th>
                  <th className="px-4 py-3">CRM Stage</th>
                  <th className="px-4 py-3">Referral / Contact</th>
                  <th className="px-4 py-3">Scheduled Loops</th>
                  <th className="px-4 py-3">Risk-Adjusted TC/yr</th>
                  <th className="px-4 py-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-800/70">
                {crm.records.map((r: any) => {
                  const base = Number(r.offer?.base || 0);
                  const eq = Number(r.offer?.equity_annual || 0);
                  const isOpt = r.offer?.equity_type === "Options";
                  const riskAdj = base + (isOpt ? eq * riskHaircut : eq);
                  return (
                    <tr key={r.target_id} className="hover:bg-zinc-900/80">
                      <td className="px-4 py-3 text-white font-semibold">
                        {r.company} — <span className="text-zinc-400 font-normal">{r.role_title}</span>
                      </td>
                      <td className="px-4 py-3">
                        <span className="rounded bg-zinc-800 px-2 py-0.5 text-sky-300">{r.app_stage}</span>
                      </td>
                      <td className="px-4 py-3 text-zinc-300">{r.referral_contact || "—"}</td>
                      <td className="px-4 py-3 text-zinc-300">
                        {r.interview_dates?.length ? r.interview_dates.join(", ") : "None"}
                      </td>
                      <td className="px-4 py-3 text-emerald-300">
                        {riskAdj > 0
                          ? `$${Math.round(riskAdj).toLocaleString()} (${r.offer?.equity_type || "RSU"})`
                          : "—"}
                      </td>
                      <td className="px-4 py-3 text-right">
                        <button
                          type="button"
                          onClick={() => {
                            setEditingCrm({
                              ...r,
                              interview_dates: [...(r.interview_dates || [])],
                              offer: { base: 0, equity_annual: 0, equity_type: "RSU", ...(r.offer || {}) },
                            });
                            setDateInput("");
                          }}
                          className="rounded border border-zinc-700 bg-zinc-800 px-2.5 py-1 text-[11px] text-white hover:bg-zinc-700"
                        >
                          Edit CRM / Offer
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          <div className="flex items-center gap-3 font-mono text-xs text-zinc-400">
            <DollarSign className="h-3.5 w-3.5 text-amber-400" />
            <span>Startup Options Liquidity Haircut: {Math.round(riskHaircut * 100)}%</span>
            <input
              type="range"
              min={0.1}
              max={1.0}
              step={0.1}
              value={riskHaircut}
              onChange={(e) => setRiskHaircut(Number(e.target.value))}
              className="w-36 accent-amber-400"
            />
            <Link href="/sandboxes" className="ml-auto flex items-center gap-1 text-emerald-400 hover:underline">
              <Sliders className="h-3.5 w-3.5" /> Interactive Systems Sandboxes →
            </Link>
          </div>
        </section>
      )}

      {/* CRM & Offer Edit Modal */}
      {editingCrm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 p-4">
          <div className="w-full max-w-lg rounded-xl border border-zinc-700 bg-zinc-900 p-6 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-base font-bold text-white">
                CRM & Offer — {editingCrm.company} ({editingCrm.role_title})
              </h3>
              <button type="button" onClick={() => setEditingCrm(null)} className="text-zinc-400 hover:text-white">
                ✕
              </button>
            </div>
            <div className="grid grid-cols-2 gap-3 text-xs">
              <label className="space-y-1">
                <span className="font-mono text-zinc-400">Application Stage</span>
                <select
                  value={editingCrm.app_stage}
                  onChange={(e) => setEditingCrm({ ...editingCrm, app_stage: e.target.value })}
                  className="w-full rounded border border-zinc-700 bg-zinc-950 px-2.5 py-2 text-white"
                >
                  {CRM_STAGES.map((st) => (
                    <option key={st} value={st}>{st}</option>
                  ))}
                </select>
              </label>
              <label className="space-y-1">
                <span className="font-mono text-zinc-400">Referral / HM Contact</span>
                <input
                  value={editingCrm.referral_contact}
                  onChange={(e) => setEditingCrm({ ...editingCrm, referral_contact: e.target.value })}
                  placeholder="Name / X handle / email"
                  className="w-full rounded border border-zinc-700 bg-zinc-950 px-2.5 py-2 text-white"
                />
              </label>
            </div>

            <div className="space-y-1 text-xs">
              <span className="font-mono text-zinc-400">Cold-Email / Outreach Draft</span>
              <textarea
                rows={2}
                value={editingCrm.cold_email_draft}
                onChange={(e) => setEditingCrm({ ...editingCrm, cold_email_draft: e.target.value })}
                placeholder="Why this specific team's work genuinely excites you..."
                className="w-full rounded border border-zinc-700 bg-zinc-950 p-2 text-white"
              />
            </div>

            <div className="space-y-2 text-xs">
              <span className="font-mono text-zinc-400">Scheduled Interview Dates (Burnout Spacing Guardrail)</span>
              <div className="flex gap-2">
                <input
                  type="date"
                  value={dateInput}
                  onChange={(e) => setDateInput(e.target.value)}
                  className="rounded border border-zinc-700 bg-zinc-950 px-2.5 py-1.5 text-white"
                />
                <button
                  type="button"
                  onClick={() => {
                    if (!dateInput) return;
                    setEditingCrm({
                      ...editingCrm,
                      interview_dates: [...editingCrm.interview_dates, dateInput],
                    });
                    setDateInput("");
                  }}
                  className="rounded bg-zinc-800 px-3 py-1.5 text-white hover:bg-zinc-700"
                >
                  + Add Loop Date
                </button>
              </div>
              <div className="flex flex-wrap gap-1.5">
                {editingCrm.interview_dates.map((d: string, i: number) => (
                  <button
                    key={`${d}-${i}`}
                    type="button"
                    onClick={() =>
                      setEditingCrm({
                        ...editingCrm,
                        interview_dates: editingCrm.interview_dates.filter((_: any, idx: number) => idx !== i),
                      })
                    }
                    className="rounded border border-zinc-700 bg-zinc-950 px-2 py-0.5 font-mono text-[11px] text-zinc-300 hover:border-rose-500"
                  >
                    {d} ✕
                  </button>
                ))}
              </div>
            </div>

            <div className="grid grid-cols-3 gap-2 text-xs">
              <label className="space-y-1">
                <span className="font-mono text-zinc-400">Base ($/yr)</span>
                <input
                  type="number"
                  value={editingCrm.offer.base || 0}
                  onChange={(e) =>
                    setEditingCrm({ ...editingCrm, offer: { ...editingCrm.offer, base: Number(e.target.value) } })
                  }
                  className="w-full rounded border border-zinc-700 bg-zinc-950 px-2 py-1.5 text-white"
                />
              </label>
              <label className="space-y-1">
                <span className="font-mono text-zinc-400">Equity ($/yr)</span>
                <input
                  type="number"
                  value={editingCrm.offer.equity_annual || 0}
                  onChange={(e) =>
                    setEditingCrm({
                      ...editingCrm,
                      offer: { ...editingCrm.offer, equity_annual: Number(e.target.value) },
                    })
                  }
                  className="w-full rounded border border-zinc-700 bg-zinc-950 px-2 py-1.5 text-white"
                />
              </label>
              <label className="space-y-1">
                <span className="font-mono text-zinc-400">Type</span>
                <select
                  value={editingCrm.offer.equity_type || "RSU"}
                  onChange={(e) =>
                    setEditingCrm({ ...editingCrm, offer: { ...editingCrm.offer, equity_type: e.target.value } })
                  }
                  className="w-full rounded border border-zinc-700 bg-zinc-950 px-2 py-1.5 text-white"
                >
                  <option value="RSU">Public RSU</option>
                  <option value="Options">Startup Options</option>
                </select>
              </label>
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => setEditingCrm(null)}
                className="rounded-lg border border-zinc-700 px-3 py-1.5 text-xs text-zinc-300"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={saveCrmRecord}
                className="rounded-lg bg-emerald-600 px-4 py-1.5 text-xs font-semibold text-white hover:bg-emerald-500"
              >
                Save CRM Record
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
