"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import {
  Lock,
  CheckCircle2,
  Clock,
  Play,
  Flag,
  Award,
  BarChart3,
  AlertTriangle,
  RefreshCw,
} from "lucide-react";
import { apiFetch } from "@/lib/api";
import { CodeEditorBox } from "@/components/CodeEditorBox";

export default function StudioGauntletPage() {
  const params = useParams<{ targetId: string }>();
  const targetId = params?.targetId || "";
  const router = useRouter();

  const [session, setSession] = useState<any>(null);
  const [activeStage, setActiveStage] = useState<number>(1);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  // Stage 1 state
  const [s1Selected, setS1Selected] = useState<string>("");
  const [s1CodeMap, setS1CodeMap] = useState<Record<string, string>>({});
  const [s1MathMap, setS1MathMap] = useState<Record<string, Record<string, string>>>({});
  const [s1Eval, setS1Eval] = useState<any>(null);

  // Stage 2 state (with dynamic countdown timer)
  const [s2Code, setS2Code] = useState("");
  const [s2Elapsed, setS2Elapsed] = useState(0);
  const [s2Sd, setS2Sd] = useState("");
  const [s2Shift, setS2Shift] = useState("");
  const [s2Dk, setS2Dk] = useState("");

  // Stage 3 & Stage 4 answers
  const [s3Ans, setS3Ans] = useState<Record<string, string>>({});
  const [s4Ans, setS4Ans] = useState<Record<string, string>>({});
  const [s4Mode, setS4Mode] = useState<"behavioral" | "research_vision">("behavioral");

  const initOrResume = async (forceNew = false) => {
    if (!targetId) return;
    setErr(null);
    const tRes = await apiFetch("/api/targets");
    const target = (tRes.targets || []).find((t: any) => t.id === targetId);
    let sessData: any;
    if (!forceNew && target?.sessions?.[0] && target.sessions[0].status === "active") {
      sessData = await apiFetch(`/api/studio/sessions/${target.sessions[0].id}`);
    } else {
      sessData = await apiFetch("/api/studio/sessions", {
        method: "POST",
        body: JSON.stringify({ target_id: targetId }),
      });
    }
    hydrateLocal(sessData);
  };

  const hydrateLocal = (sessData: any) => {
    setSession(sessData);
    setActiveStage(sessData.current_stage || 1);
    const s1Ids = [
      ...(sessData.plan.stage1.track_1a_overlap_ids || []),
      ...(sessData.plan.stage1.track_1b_gap_ids || []),
    ];
    if (s1Ids.length > 0 && !s1Selected) setS1Selected(s1Ids[0]);
    const cmap: Record<string, string> = {};
    for (const id of s1Ids) {
      cmap[id] = sessData.hydrated_items[id]?.starter_code || "";
    }
    setS1CodeMap((prev) => ({ ...cmap, ...prev }));
    const s2Cid = sessData.plan.stage2.coding_item_id;
    if (s2Cid && !s2Code) {
      setS2Code(sessData.hydrated_items[s2Cid]?.starter_code || "");
    }
  };

  useEffect(() => {
    initOrResume(false).catch((e) => setErr(e.message));
  }, [targetId]);

  // Dynamic Stage 2 Timer
  useEffect(() => {
    if (activeStage !== 2 || !session || session.stage_results["2"].passed) return;
    const id = setInterval(() => setS2Elapsed((s) => s + 1), 1000);
    return () => clearInterval(id);
  }, [activeStage, session]);

  if (err) {
    return (
      <div className="rounded-xl border border-rose-500/40 bg-rose-500/10 p-6 text-sm text-rose-200">
        {err}
      </div>
    );
  }
  if (!session) {
    return <div className="py-12 text-center font-mono text-sm text-zinc-500">Generating personalized 4-stage gauntlet...</div>;
  }

  const { plan, stage_results: sr, hydrated_items: items } = session;
  const s1Overlap: string[] = plan.stage1.track_1a_overlap_ids || [];
  const s1Gaps: string[] = plan.stage1.track_1b_gap_ids || [];
  const s1ActiveItem = items[s1Selected];

  const handleStage1Submit = async () => {
    if (!s1ActiveItem) return;
    setBusy(true);
    setS1Eval(null);
    try {
      const res = await apiFetch(`/api/studio/sessions/${session.id}/stage1/${s1ActiveItem.id}`, {
        method: "POST",
        body: JSON.stringify({
          code: s1ActiveItem.kind === "math" ? null : s1CodeMap[s1ActiveItem.id] || "",
          math_answers: s1ActiveItem.kind === "math" ? s1MathMap[s1ActiveItem.id] || {} : null,
        }),
      });
      setS1Eval(res.evaluation);
      setSession(res.session);
      if (res.session.stage_results["2"].unlocked && activeStage === 1) {
        // Auto-highlight unlock banner
      }
    } finally {
      setBusy(false);
    }
  };

  const handleStage2Submit = async () => {
    setBusy(true);
    try {
      const res = await apiFetch(`/api/studio/sessions/${session.id}/stage2`, {
        method: "POST",
        body: JSON.stringify({
          coding_code: s2Code,
          coding_duration_sec: s2Elapsed,
          system_design_answer: s2Sd,
          constraint_shift_answer: s2Shift,
          deep_knowledge_answer: s2Dk,
        }),
      });
      setSession(res.session);
    } catch (e: any) {
      setErr(e.message);
    } finally {
      setBusy(false);
    }
  };

  const handleStage3Submit = async () => {
    setBusy(true);
    try {
      const res = await apiFetch(`/api/studio/sessions/${session.id}/stage3`, {
        method: "POST",
        body: JSON.stringify({ answers: s3Ans }),
      });
      setSession(res.session);
    } finally {
      setBusy(false);
    }
  };

  const handleStage4Submit = async () => {
    setBusy(true);
    try {
      const res = await apiFetch(`/api/studio/sessions/${session.id}/stage4`, {
        method: "POST",
        body: JSON.stringify({ answers: s4Ans, track_mode: s4Mode }),
      });
      setSession(res.session);
    } finally {
      setBusy(false);
    }
  };

  const handleAbort = async () => {
    await apiFetch(`/api/studio/sessions/${session.id}/abort`, { method: "POST" });
    router.push(`/recap/${session.id}`);
  };

  const s2Limit = plan.stage2.coding_time_limit_sec || 1200;
  const s2Remaining = Math.max(0, s2Limit - s2Elapsed);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-zinc-800 pb-4">
        <div>
          <p className="font-mono text-xs uppercase text-emerald-400">
            Interview Studio · {plan.company} ({plan.seniority})
          </p>
          <h1 className="text-2xl font-bold text-white">{plan.role_title}</h1>
        </div>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => initOrResume(true)}
            className="flex items-center gap-1 rounded-lg border border-zinc-700 px-3 py-1.5 font-mono text-xs text-zinc-300 hover:bg-zinc-800"
          >
            <RefreshCw className="h-3.5 w-3.5" /> New Attempt
          </button>
          <button
            type="button"
            onClick={handleAbort}
            className="flex items-center gap-1 rounded-lg border border-rose-500/40 bg-rose-500/10 px-3 py-1.5 font-mono text-xs text-rose-300 hover:bg-rose-500/20"
          >
            <Flag className="h-3.5 w-3.5" /> Abort → Prep Recap
          </button>
          <Link
            href={`/recap/${session.id}`}
            className="flex items-center gap-1 rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-1.5 font-mono text-xs text-zinc-200 hover:bg-zinc-800"
          >
            <BarChart3 className="h-3.5 w-3.5" /> Recap
          </Link>
          <Link
            href={`/readiness/${targetId}`}
            className={`flex items-center gap-1 rounded-lg px-3 py-1.5 font-mono text-xs font-semibold ${
              session.status === "completed"
                ? "bg-emerald-600 text-white hover:bg-emerald-500"
                : "border border-zinc-800 bg-zinc-950 text-zinc-500"
            }`}
          >
            <Award className="h-3.5 w-3.5" /> Readiness Score
          </Link>
        </div>
      </div>

      {/* 4-Stage Gated Stepper */}
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-4">
        {[
          { n: 1, label: "Stage 1: JD/CV Baseline" },
          { n: 2, label: "Stage 2: Technical Gauntlet" },
          { n: 3, label: "Stage 3: Project Deep-Dive" },
          { n: 4, label: "Stage 4: Behavioral" },
        ].map((st) => {
          const r = sr[String(st.n)];
          const unlocked = !!r?.unlocked;
          const passed = !!r?.passed;
          return (
            <button
              key={st.n}
              type="button"
              disabled={!unlocked}
              onClick={() => unlocked && setActiveStage(st.n)}
              className={`flex items-center justify-between rounded-xl border p-3.5 text-left transition-all ${
                activeStage === st.n
                  ? "border-emerald-500 bg-emerald-500/10"
                  : unlocked
                  ? "border-zinc-700 bg-zinc-900/70 hover:border-zinc-500"
                  : "cursor-not-allowed border-zinc-900 bg-zinc-950 opacity-50"
              }`}
            >
              <div>
                <p className="font-mono text-xs font-bold text-white">{st.label}</p>
                <p className="font-mono text-[11px] text-zinc-400">
                  {passed ? `PASSED · ${r.score}%` : unlocked ? `UNLOCKED · ${r.score || 0}%` : "LOCKED"}
                </p>
              </div>
              {passed ? (
                <CheckCircle2 className="h-5 w-5 text-emerald-400 shrink-0" />
              ) : !unlocked ? (
                <Lock className="h-4 w-4 text-zinc-600 shrink-0" />
              ) : (
                <span className="h-2.5 w-2.5 rounded-full bg-amber-400 shrink-0" />
              )}
            </button>
          );
        })}
      </div>

      {/* STAGE 1: Dual-Zone Targeted JD/CV Refresher */}
      {activeStage === 1 && (
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
          <div className="rounded-xl border border-zinc-800 bg-zinc-900/60 p-4 space-y-4">
            <div>
              <h2 className="text-sm font-bold text-white">{plan.stage1.title}</h2>
              <p className="mt-1 text-xs text-zinc-400">
                Non-negotiable baseline: pass every item below (even if Core Syllabus is 100%) to unlock Stage 2.
              </p>
            </div>

            <div className="space-y-2">
              <p className="font-mono text-[11px] font-bold uppercase text-sky-400">
                Track 1A — Claim Defense (CV ∩ JD)
              </p>
              {s1Overlap.map((id) => {
                const it = items[id];
                const st = sr["1"].items?.[id];
                return (
                  <button
                    key={id}
                    type="button"
                    onClick={() => {
                      setS1Selected(id);
                      setS1Eval(null);
                    }}
                    className={`flex w-full items-center justify-between rounded-lg border px-3 py-2 text-left text-xs ${
                      s1Selected === id
                        ? "border-sky-500 bg-sky-500/15 text-white"
                        : "border-zinc-800 bg-zinc-950 text-zinc-300"
                    }`}
                  >
                    <span className="truncate">{it?.title || id}</span>
                    {st?.passed && <CheckCircle2 className="h-4 w-4 text-emerald-400 shrink-0" />}
                  </button>
                );
              })}
            </div>

            <div className="space-y-2">
              <p className="font-mono text-[11px] font-bold uppercase text-amber-400">
                Track 1B — Blind-Spot Triage (JD \ CV)
              </p>
              {s1Gaps.map((id) => {
                const it = items[id];
                const st = sr["1"].items?.[id];
                return (
                  <button
                    key={id}
                    type="button"
                    onClick={() => {
                      setS1Selected(id);
                      setS1Eval(null);
                    }}
                    className={`flex w-full items-center justify-between rounded-lg border px-3 py-2 text-left text-xs ${
                      s1Selected === id
                        ? "border-amber-500 bg-amber-500/15 text-white"
                        : "border-zinc-800 bg-zinc-950 text-zinc-300"
                    }`}
                  >
                    <span className="truncate">{it?.title || id}</span>
                    {st?.passed && <CheckCircle2 className="h-4 w-4 text-emerald-400 shrink-0" />}
                  </button>
                );
              })}
            </div>

            {sr["2"].unlocked && (
              <button
                type="button"
                onClick={() => setActiveStage(2)}
                className="w-full rounded-lg bg-emerald-600 py-2 text-xs font-bold text-white hover:bg-emerald-500"
              >
                Stage 1 Cleared! Proceed to Stage 2 →
              </button>
            )}
          </div>

          <div className="lg:col-span-2 rounded-xl border border-zinc-800 bg-zinc-900/60 p-5 space-y-4">
            {s1ActiveItem && (
              <>
                <div className="flex items-center justify-between">
                  <h3 className="text-base font-bold text-white">{s1ActiveItem.title}</h3>
                  <span className="rounded bg-zinc-800 px-2 py-0.5 font-mono text-xs uppercase text-zinc-300">
                    {s1ActiveItem.kind}
                  </span>
                </div>
                <pre className="whitespace-pre-wrap font-sans text-xs leading-relaxed text-zinc-300 max-h-48 overflow-y-auto rounded-lg border border-zinc-800 bg-zinc-950 p-3">
                  {s1ActiveItem.kind === "math"
                    ? s1ActiveItem.worked_example_md
                    : s1ActiveItem.prompt_md}
                </pre>

                {s1ActiveItem.kind === "math" ? (
                  <div className="space-y-3">
                    {(s1ActiveItem.drills || []).map((d: any) => (
                      <div key={d.id} className="space-y-1">
                        <p className="text-xs text-zinc-200">{d.prompt}</p>
                        <input
                          value={(s1MathMap[s1ActiveItem.id] || {})[d.id] || ""}
                          onChange={(e) =>
                            setS1MathMap((prev) => ({
                              ...prev,
                              [s1ActiveItem.id]: {
                                ...(prev[s1ActiveItem.id] || {}),
                                [d.id]: e.target.value,
                              },
                            }))
                          }
                          className="w-full rounded border border-zinc-700 bg-zinc-950 px-3 py-1.5 font-mono text-xs text-white"
                        />
                      </div>
                    ))}
                  </div>
                ) : (
                  <CodeEditorBox
                    value={s1CodeMap[s1ActiveItem.id] || ""}
                    onChange={(v) =>
                      setS1CodeMap((prev) => ({ ...prev, [s1ActiveItem.id]: v }))
                    }
                    height="280px"
                  />
                )}

                <div className="flex items-center justify-between">
                  <button
                    type="button"
                    onClick={handleStage1Submit}
                    disabled={busy}
                    className="flex items-center gap-1.5 rounded-lg bg-emerald-600 px-4 py-2 text-xs font-semibold text-white hover:bg-emerald-500 disabled:opacity-50"
                  >
                    <Play className="h-3.5 w-3.5" />
                    {busy ? "Verifying..." : "Submit Stage 1 Item"}
                  </button>
                  {s1Eval && (
                    <span
                      className={`font-mono text-xs font-bold ${
                        s1Eval.passed ? "text-emerald-400" : "text-rose-400"
                      }`}
                    >
                      {s1Eval.passed ? "PASSED" : `FAILED: ${s1Eval.stderr || "Check tests/counterexamples"}`}
                    </span>
                  )}
                </div>
              </>
            )}
          </div>
        </div>
      )}

      {/* STAGE 2: Senior/Staff Technical Gauntlet */}
      {activeStage === 2 && (
        <div className="space-y-6 rounded-xl border border-zinc-800 bg-zinc-900/60 p-6">
          <div className="flex flex-wrap items-center justify-between gap-2 border-b border-zinc-800 pb-3">
            <div>
              <h2 className="text-lg font-bold text-white">{plan.stage2.title}</h2>
              <p className="text-xs text-zinc-400">
                Zero hand-holding: timed coding snippet + whiteboard System Design with mid-flight constraint shift + Staff deep knowledge.
              </p>
            </div>
            <div className="flex items-center gap-2 rounded-lg border border-amber-500/40 bg-amber-500/10 px-3 py-1.5 font-mono text-xs text-amber-300">
              <Clock className="h-4 w-4" />
              <span>
                Time Remaining: {Math.floor(s2Remaining / 60)}:
                {(s2Remaining % 60).toString().padStart(2, "0")}
              </span>
            </div>
          </div>

          {/* 2A: Timed Coding */}
          {plan.stage2.coding_item_id && (
            <div className="space-y-2">
              <h3 className="font-mono text-xs font-bold uppercase text-emerald-400">
                2A. Dynamically Timed Coding — {items[plan.stage2.coding_item_id]?.title}
              </h3>
              <pre className="whitespace-pre-wrap rounded-lg border border-zinc-800 bg-zinc-950 p-3 font-sans text-xs text-zinc-300 max-h-40 overflow-y-auto">
                {items[plan.stage2.coding_item_id]?.prompt_md}
              </pre>
              <CodeEditorBox value={s2Code} onChange={setS2Code} height="260px" />
            </div>
          )}

          {/* 2B: System Design + Mid-Flight Constraint Shift */}
          <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
            <div className="space-y-2">
              <h3 className="font-mono text-xs font-bold uppercase text-sky-400">
                2B. Whiteboard System Design (Include Diagram + FLOP/HBM Math)
              </h3>
              <p className="text-xs text-zinc-300">{plan.stage2.system_design.prompt}</p>
              <textarea
                rows={7}
                value={s2Sd}
                onChange={(e) => setS2Sd(e.target.value)}
                placeholder="Write architecture diagram (Mermaid/ASCII), HBM/bandwidth calculations, bottlenecks, and trade-offs..."
                className="w-full rounded-lg border border-zinc-700 bg-zinc-950 p-3 font-mono text-xs text-zinc-100"
              />
            </div>
            <div className="space-y-2">
              <h3 className="flex items-center gap-1.5 font-mono text-xs font-bold uppercase text-amber-400">
                <AlertTriangle className="h-3.5 w-3.5" /> Mid-Flight Constraint Shift
              </h3>
              <p className="text-xs text-amber-200/90">{plan.stage2.system_design.constraint_shift}</p>
              <textarea
                rows={7}
                value={s2Shift}
                onChange={(e) => setS2Shift(e.target.value)}
                placeholder="Explain quantitatively what breaks first and how you redesign to preserve p99 SLA..."
                className="w-full rounded-lg border border-amber-500/30 bg-zinc-950 p-3 font-mono text-xs text-zinc-100"
              />
            </div>
          </div>

          {/* 2C: Staff Deep Knowledge */}
          <div className="space-y-2">
            <h3 className="font-mono text-xs font-bold uppercase text-violet-400">
              2C. Staff-Level Deep Knowledge & Edge-Case Probe
            </h3>
            <p className="text-xs text-zinc-300">{plan.stage2.deep_knowledge.prompt}</p>
            <textarea
              rows={4}
              value={s2Dk}
              onChange={(e) => setS2Dk(e.target.value)}
              placeholder="Detail exact failure modes, when optimizations regress latency/accuracy, and profiling proof..."
              className="w-full rounded-lg border border-zinc-700 bg-zinc-950 p-3 font-mono text-xs text-zinc-100"
            />
          </div>

          <div className="flex items-center justify-between pt-2">
            <button
              type="button"
              onClick={handleStage2Submit}
              disabled={busy}
              className="rounded-lg bg-emerald-600 px-5 py-2.5 text-xs font-bold text-white hover:bg-emerald-500 disabled:opacity-50"
            >
              {busy ? "Grading Stage 2 Gauntlet..." : "Submit Stage 2 Gauntlet"}
            </button>
            {sr["2"].system_design && (
              <div className="text-right font-mono text-xs">
                <p className={sr["2"].passed ? "text-emerald-400 font-bold" : "text-rose-400 font-bold"}>
                  Stage 2 Score: {sr["2"].score}% ({sr["2"].passed ? "PASSED — Stage 3 Unlocked" : "Below 75% Bar — Refine & Resubmit"})
                </p>
                <p className="text-zinc-400">{sr["2"].system_design.feedback}</p>
              </div>
            )}
          </div>
          {sr["3"].unlocked && (
            <button
              type="button"
              onClick={() => setActiveStage(3)}
              className="rounded-lg bg-sky-600 px-4 py-2 text-xs font-bold text-white hover:bg-sky-500"
            >
              Proceed to Stage 3: Project Deep-Dive →
            </button>
          )}
        </div>
      )}

      {/* STAGE 3: CV Project Deep-Dive */}
      {activeStage === 3 && (
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
          <div className="rounded-xl border border-zinc-800 bg-zinc-900/60 p-4 space-y-3">
            <p className="font-mono text-xs font-bold uppercase text-amber-400">
              Interrogated CV Project & Private Dossier
            </p>
            <h3 className="text-sm font-bold text-white">{plan.stage3.project_title}</h3>
            <pre className="whitespace-pre-wrap rounded-lg border border-zinc-800 bg-zinc-950 p-3 font-mono text-[11px] text-zinc-400 max-h-80 overflow-y-auto">
              {plan.stage3.dossier_excerpt || plan.stage3.project_summary}
            </pre>
          </div>

          <div className="lg:col-span-2 rounded-xl border border-zinc-800 bg-zinc-900/60 p-6 space-y-5">
            <h2 className="text-lg font-bold text-white">{plan.stage3.title}</h2>
            {plan.stage3.questions.map((q: any) => {
              const j = sr["3"].answers?.[q.id];
              return (
                <div key={q.id} className="space-y-2">
                  <p className="text-sm font-semibold text-zinc-100">{q.title}</p>
                  <p className="text-xs text-zinc-400">{q.prompt}</p>
                  <textarea
                    rows={5}
                    value={s3Ans[q.id] || ""}
                    onChange={(e) => setS3Ans((prev) => ({ ...prev, [q.id]: e.target.value }))}
                    placeholder="Defend architecture choices with exact latency/HBM numbers, rejected alternatives, and scaling limits..."
                    className="w-full rounded-lg border border-zinc-700 bg-zinc-950 p-3 font-mono text-xs text-zinc-100"
                  />
                  {j && (
                    <div className="rounded-lg border border-zinc-800 bg-zinc-950 p-3 font-mono text-xs space-y-1">
                      <p className={j.passed ? "text-emerald-400" : "text-rose-400"}>
                        Score: {j.score}% · {j.feedback}
                      </p>
                      <p className="text-amber-300">Adversarial Follow-Up: {j.follow_up_probe}</p>
                    </div>
                  )}
                </div>
              );
            })}
            <div className="flex items-center gap-3">
              <button
                type="button"
                onClick={handleStage3Submit}
                disabled={busy}
                className="rounded-lg bg-emerald-600 px-5 py-2 text-xs font-bold text-white hover:bg-emerald-500"
              >
                {busy ? "Evaluating Defense..." : "Submit Stage 3 Defense"}
              </button>
              {sr["4"].unlocked && (
                <button
                  type="button"
                  onClick={() => setActiveStage(4)}
                  className="rounded-lg bg-sky-600 px-4 py-2 text-xs font-bold text-white hover:bg-sky-500"
                >
                  Proceed to Stage 4: Behavioral →
                </button>
              )}
            </div>
          </div>
        </div>
      )}

      {/* STAGE 4: Managerial & Behavioral (4A) OR Research Vision & Taste (4B) */}
      {activeStage === 4 && (
        <div className="rounded-xl border border-zinc-800 bg-zinc-900/60 p-6 space-y-5">
          <div className="flex flex-wrap items-center justify-between gap-3 border-b border-zinc-800 pb-3">
            <div>
              <h2 className="text-lg font-bold text-white">{plan.stage4.title}</h2>
              <p className="text-xs text-zinc-400">
                Switch between Stage 4A (Staff Leadership/Conflict) and Stage 4B (Research Vision, 2-Year Horizon & Day-1 Experiment Pitch).
              </p>
            </div>
            <div className="flex items-center gap-1 rounded-lg border border-zinc-800 bg-zinc-950 p-1 font-mono text-xs">
              <button
                type="button"
                onClick={() => setS4Mode("behavioral")}
                className={`rounded px-3 py-1 ${
                  s4Mode === "behavioral"
                    ? "bg-emerald-600 text-white font-semibold"
                    : "text-zinc-400 hover:text-white"
                }`}
              >
                4A: Behavioral & Leadership
              </button>
              <button
                type="button"
                onClick={() => setS4Mode("research_vision")}
                className={`rounded px-3 py-1 ${
                  s4Mode === "research_vision"
                    ? "bg-violet-600 text-white font-semibold"
                    : "text-zinc-400 hover:text-white"
                }`}
              >
                4B: Research Vision & Taste
              </button>
            </div>
          </div>
          {(s4Mode === "research_vision"
            ? plan.stage4.research_questions || plan.stage4.questions
            : plan.stage4.questions
          ).map((q: any) => {
            const j = sr["4"].answers?.[q.id];
            return (
              <div key={q.id} className="space-y-2">
                <p className="text-sm font-semibold text-zinc-100">{q.title}</p>
                <p className="text-xs text-zinc-400">{q.prompt}</p>
                <textarea
                  rows={5}
                  value={s4Ans[q.id] || ""}
                  onChange={(e) => setS4Ans((prev) => ({ ...prev, [q.id]: e.target.value }))}
                  placeholder={
                    s4Mode === "research_vision"
                      ? "State your contrarian thesis, falsifiable hypothesis, baseline, ablation matrix, compute budget, and kill criteria..."
                      : "Structure with STAR: Situation, Task, Staff-level Action (RFC/alignment/trade-off), Quantified Result..."
                  }
                  className="w-full rounded-lg border border-zinc-700 bg-zinc-950 p-3 font-mono text-xs text-zinc-100"
                />
                {j && (
                  <p className={`font-mono text-xs ${j.passed ? "text-emerald-400" : "text-rose-400"}`}>
                    Score: {j.score}% · {j.feedback}
                  </p>
                )}
              </div>
            );
          })}

          <div className="flex flex-wrap items-center gap-3">
            <button
              type="button"
              onClick={handleStage4Submit}
              disabled={busy}
              className="rounded-lg bg-emerald-600 px-5 py-2 text-xs font-bold text-white hover:bg-emerald-500"
            >
              {busy ? "Finalizing Stage 4..." : "Complete Stage 4 & Unlock Readiness"}
            </button>
            {session.status === "completed" && (
              <>
                <Link
                  href={`/recap/${session.id}`}
                  className="rounded-lg border border-zinc-700 bg-zinc-900 px-4 py-2 text-xs font-semibold text-zinc-200 hover:bg-zinc-800"
                >
                  View Prep Recap →
                </Link>
                <Link
                  href={`/readiness/${targetId}`}
                  className="rounded-lg bg-amber-500 px-4 py-2 text-xs font-bold text-zinc-950 hover:bg-amber-400"
                >
                  Open Final Readiness Verdict →
                </Link>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
