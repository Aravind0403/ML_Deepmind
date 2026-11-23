"use client";

import Link from "next/link";
import { useParams, useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";
import {
  ArrowLeft,
  Play,
  RotateCcw,
  Eye,
  CheckCircle2,
  XCircle,
  ShieldCheck,
  Clock,
  Flag,
  NotebookPen,
  Save,
} from "lucide-react";
import { apiFetch } from "@/lib/api";
import { CodeEditorBox } from "@/components/CodeEditorBox";
import { YouTubeCheckpointPlayer } from "@/components/YouTubeCheckpointPlayer";

export default function SyllabusItemPage() {
  const params = useParams<{ itemId: string }>();
  const itemId = params?.itemId || "";
  const searchParams = useSearchParams();
  const isReview = searchParams ? searchParams.get("review") === "1" : false;
  const isSpeedRun = searchParams ? searchParams.get("speedrun") === "1" : false;

  const [item, setItem] = useState<any>(null);
  const [code, setCode] = useState("");
  const [mathAnswers, setMathAnswers] = useState<Record<string, string>>({});
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [tab, setTab] = useState<"prompt" | "theory" | "video" | "notes">("prompt");
  const [showRef, setShowRef] = useState(false);

  // Predict-Before-Running (Expected / Observed / Why) scratchpad
  const [notes, setNotes] = useState({ expected_text: "", observed_text: "", why_text: "" });
  const [noteSaved, setNoteSaved] = useState<string | null>(null);

  // 20-Min Speed-Run Timer & 15-Min Stuck Cutoff
  const [elapsedSec, setElapsedSec] = useState(0);
  const [stuckMsg, setStuckMsg] = useState<string | null>(null);

  useEffect(() => {
    if (!itemId) return;
    apiFetch(`/api/items/${itemId}`).then((d) => {
      setItem(d);
      const draft = typeof window !== "undefined" ? localStorage.getItem(`draft_${itemId}`) : null;
      setCode(draft || d.last_code || d.starter_code || "");
    });
    apiFetch(`/api/items/${itemId}/notes`)
      .then((n) =>
        setNotes({
          expected_text: n.expected_text || "",
          observed_text: n.observed_text || "",
          why_text: n.why_text || "",
        })
      )
      .catch(() => {});
  }, [itemId]);

  useEffect(() => {
    if (!itemId || !code) return;
    try {
      localStorage.setItem(`draft_${itemId}`, code);
    } catch {}
  }, [itemId, code]);

  useEffect(() => {
    if (!isSpeedRun) return;
    const id = setInterval(() => setElapsedSec((s) => s + 1), 1000);
    return () => clearInterval(id);
  }, [isSpeedRun]);

  const saveNotes = async () => {
    if (!itemId) return;
    await apiFetch(`/api/items/${itemId}/notes`, {
      method: "PUT",
      body: JSON.stringify(notes),
    });
    setNoteSaved("Saved Expected / Observed / Why record locally.");
    setTimeout(() => setNoteSaved(null), 2500);
  };

  const flagStuck = async () => {
    if (!itemId) return;
    const res = await apiFetch(`/api/syllabus/flag-stuck/${itemId}`, { method: "POST" });
    setStuckMsg(res.message);
    setShowRef(true);
  };

  const handleRun = async () => {
    if (!itemId) return;
    setRunning(true);
    setResult(null);
    try {
      const res = await apiFetch(`/api/items/${itemId}/evaluate`, {
        method: "POST",
        body: JSON.stringify({
          code: item.kind === "math" ? null : code,
          math_answers: item.kind === "math" ? mathAnswers : null,
          is_review: isReview,
        }),
      });
      setResult(res);
    } catch (e: any) {
      setResult({ evaluation: { passed: false, stderr: e.message } });
    } finally {
      setRunning(false);
    }
  };

  if (!item) {
    return <div className="py-12 text-center font-mono text-sm text-zinc-500">Loading exercise...</div>;
  }

  const ev = result?.evaluation;

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-zinc-800 pb-4">
        <div className="space-y-1">
          <Link
            href="/syllabus"
            className="inline-flex items-center gap-1 font-mono text-xs text-zinc-400 hover:text-zinc-200"
          >
            <ArrowLeft className="h-3.5 w-3.5" /> Back to Core Syllabus
          </Link>
          <div className="flex items-center gap-2.5">
            <h1 className="text-xl font-bold text-white">{item.title}</h1>
            <span className="rounded bg-zinc-800 px-2 py-0.5 font-mono text-xs uppercase text-emerald-300">
              {item.kind}
            </span>
            <span className="rounded bg-zinc-900 border border-zinc-800 px-2 py-0.5 font-mono text-xs text-zinc-400">
              {item.difficulty} · +{item.xp} XP
            </span>
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-2 font-mono text-xs text-zinc-400">
          {isSpeedRun && (
            <span
              className={`flex items-center gap-1 rounded border px-2.5 py-1 ${
                elapsedSec >= 900
                  ? "border-rose-500 bg-rose-500/15 text-rose-200 font-bold"
                  : "border-orange-500/40 bg-orange-500/10 text-orange-300"
              }`}
            >
              <Clock className="h-3.5 w-3.5" />
              Speed-Run {Math.floor(elapsedSec / 60)}:{(elapsedSec % 60).toString().padStart(2, "0")} / 20:00
            </span>
          )}
          <button
            type="button"
            onClick={flagStuck}
            className="flex items-center gap-1 rounded border border-amber-500/40 bg-amber-500/10 px-2.5 py-1 text-amber-300 hover:bg-amber-500/20"
            title="Silvia Sapora 15-Min Rule: reveal reference, log Expected/Observed/Why, and flag 3x in FSRS"
          >
            <Flag className="h-3.5 w-3.5" /> Stuck (15m Cutoff → FSRS)
          </button>
          <ShieldCheck className="h-4 w-4 text-emerald-400" />
          <span className="hidden sm:inline">Sandboxed (5s + AST)</span>
        </div>
      </div>

      {stuckMsg && (
        <div className="rounded-lg border border-amber-500/40 bg-amber-500/10 px-4 py-2 text-xs text-amber-200">
          {stuckMsg}
        </div>
      )}

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Left Panel: Prompt / Theory / Video Checkpoints */}
        <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5 space-y-4">
          <div className="flex flex-wrap items-center gap-2 border-b border-zinc-800 pb-2">
            {(["prompt", "theory", "video", "notes"] as const).map((t) => (
              <button
                key={t}
                type="button"
                onClick={() => setTab(t)}
                className={`rounded-lg px-3 py-1.5 font-mono text-xs uppercase ${
                  tab === t
                    ? "bg-zinc-800 text-white font-semibold"
                    : "text-zinc-400 hover:text-zinc-200"
                }`}
              >
                {t === "video"
                  ? `Video (${item.videos?.length || 0})`
                  : t === "notes"
                  ? "Predict / Notes"
                  : t}
              </button>
            ))}
          </div>

          {tab === "prompt" && (
            <div className="space-y-4">
              <pre className="whitespace-pre-wrap font-sans text-sm leading-relaxed text-zinc-200">
                {item.kind === "math" ? item.worked_example_md : item.prompt_md}
              </pre>
              {item.milestones && item.milestones.length > 0 && (
                <div className="rounded-lg border border-zinc-800 bg-zinc-950 p-3 space-y-1.5">
                  <p className="font-mono text-xs font-bold uppercase text-rose-300">
                    Graded Project Milestones
                  </p>
                  {item.milestones.map((m: any) => (
                    <p key={m.id} className="text-xs text-zinc-300">
                      • {m.title}
                    </p>
                  ))}
                </div>
              )}
              {item.metric_name && (
                <div className="rounded-lg border border-violet-500/30 bg-violet-500/10 p-3 font-mono text-xs text-violet-200">
                  Target Lab Metric: <strong>{item.metric_name}</strong> {item.metric_goal}
                </div>
              )}
            </div>
          )}

          {tab === "theory" && (
            <pre className="whitespace-pre-wrap font-sans text-sm leading-relaxed text-zinc-300">
              {item.theory_md || item.worked_example_md || "No separate theory sheet for this item."}
            </pre>
          )}

          {tab === "video" && (
            <div className="space-y-4">
              {item.videos && item.videos.length > 0 ? (
                item.videos.map((v: any) => <YouTubeCheckpointPlayer key={v.id} video={v} />)
              ) : (
                <p className="text-xs text-zinc-400">No YouTube lecture attached to this unit yet.</p>
              )}
            </div>
          )}

          {tab === "notes" && (
            <div className="space-y-3">
              <div className="flex items-center gap-2 text-xs text-sky-300">
                <NotebookPen className="h-4 w-4" />
                <span>
                  <strong>Predict Before Running</strong> — write expected shapes/invariants first, then record surprises.
                </span>
              </div>
              <div className="space-y-1">
                <label className="font-mono text-[11px] uppercase text-zinc-400">1. Expected (Shapes, Complexity, Edge Cases)</label>
                <textarea
                  rows={3}
                  value={notes.expected_text}
                  onChange={(e) => setNotes({ ...notes, expected_text: e.target.value })}
                  placeholder="Predict output shapes, numerical invariants, and likely bugs before running..."
                  className="w-full rounded-lg border border-zinc-700 bg-zinc-950 p-2.5 font-mono text-xs text-zinc-100"
                />
              </div>
              <div className="space-y-1">
                <label className="font-mono text-[11px] uppercase text-zinc-400">2. Observed (What Actually Happened)</label>
                <textarea
                  rows={3}
                  value={notes.observed_text}
                  onChange={(e) => setNotes({ ...notes, observed_text: e.target.value })}
                  placeholder="Did tests/counterexamples surprise you?"
                  className="w-full rounded-lg border border-zinc-700 bg-zinc-950 p-2.5 font-mono text-xs text-zinc-100"
                />
              </div>
              <div className="space-y-1">
                <label className="font-mono text-[11px] uppercase text-zinc-400">3. Why (Permanent Takeaway)</label>
                <textarea
                  rows={3}
                  value={notes.why_text}
                  onChange={(e) => setNotes({ ...notes, why_text: e.target.value })}
                  placeholder="Root cause & rule-of-thumb to remember in interviews..."
                  className="w-full rounded-lg border border-zinc-700 bg-zinc-950 p-2.5 font-mono text-xs text-zinc-100"
                />
              </div>
              <div className="flex items-center gap-3">
                <button
                  type="button"
                  onClick={saveNotes}
                  className="flex items-center gap-1.5 rounded-lg bg-sky-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-sky-500"
                >
                  <Save className="h-3.5 w-3.5" /> Save Prediction Log
                </button>
                {noteSaved && <span className="text-xs text-emerald-300">{noteSaved}</span>}
              </div>
            </div>
          )}
        </div>

        {/* Right Panel: Interactive Editor / SymPy Drills + Sandbox Results */}
        <div className="space-y-4">
          {item.kind === "math" ? (
            <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5 space-y-4">
              <h2 className="font-mono text-xs font-bold uppercase text-sky-400">
                SymPy Symbolic & Numeric Practice Drills
              </h2>
              {(item.drills || []).map((d: any, idx: number) => (
                <div key={d.id} className="space-y-1.5 rounded-lg border border-zinc-800 bg-zinc-950 p-3">
                  <p className="text-sm text-zinc-200">
                    <span className="font-mono text-sky-400 mr-2">Q{idx + 1}.</span>
                    {d.prompt}
                  </p>
                  <input
                    type="text"
                    value={mathAnswers[d.id] || ""}
                    onChange={(e) =>
                      setMathAnswers((prev) => ({ ...prev, [d.id]: e.target.value }))
                    }
                    placeholder={
                      d.mode === "symbolic"
                        ? `Symbolic expression using ${(d.symbols || []).join(", ")}`
                        : "Enter numeric value..."
                    }
                    className="w-full rounded-md border border-zinc-700 bg-zinc-900 px-3 py-2 font-mono text-sm text-white"
                  />
                </div>
              ))}
              <button
                type="button"
                onClick={handleRun}
                disabled={running}
                className="flex items-center gap-2 rounded-lg bg-emerald-600 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-500 disabled:opacity-50"
              >
                <Play className="h-4 w-4" />
                {running ? "Verifying via SymPy..." : "Verify Math Drills"}
              </button>
            </div>
          ) : (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="font-mono text-xs text-zinc-400">Python 3.12 · NumPy</span>
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => {
                      if (typeof window !== "undefined") localStorage.removeItem(`draft_${itemId}`);
                      setCode(item.starter_code || "");
                    }}
                    className="flex items-center gap-1 rounded border border-zinc-700 px-2.5 py-1 font-mono text-xs text-zinc-300 hover:bg-zinc-800"
                  >
                    <RotateCcw className="h-3 w-3" /> Reset
                  </button>
                  <button
                    type="button"
                    onClick={() => setShowRef((v) => !v)}
                    className="flex items-center gap-1 rounded border border-zinc-700 px-2.5 py-1 font-mono text-xs text-zinc-300 hover:bg-zinc-800"
                  >
                    <Eye className="h-3 w-3" /> {showRef ? "Hide Reference" : "Reference"}
                  </button>
                  <button
                    type="button"
                    onClick={handleRun}
                    disabled={running}
                    className="flex items-center gap-1.5 rounded-lg bg-emerald-600 px-4 py-1.5 text-xs font-semibold text-white hover:bg-emerald-500 disabled:opacity-50"
                  >
                    <Play className="h-3.5 w-3.5" />
                    {running ? "Running..." : "Run & Grade"}
                  </button>
                </div>
              </div>

              <CodeEditorBox value={code} onChange={setCode} height="380px" />

              {showRef && (
                <div className="rounded-lg border border-zinc-800 bg-zinc-950 p-3">
                  <p className="mb-2 font-mono text-xs text-amber-400">Verified Reference Solution</p>
                  <pre className="overflow-x-auto font-mono text-xs text-zinc-300">
                    {item.reference_code}
                  </pre>
                </div>
              )}
            </div>
          )}

          {/* Evaluation Console */}
          {ev && (
            <div
              className={`rounded-xl border p-4 space-y-3 ${
                ev.passed
                  ? "border-emerald-500/50 bg-emerald-500/10"
                  : "border-rose-500/50 bg-rose-500/10"
              }`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  {ev.passed ? (
                    <CheckCircle2 className="h-5 w-5 text-emerald-400" />
                  ) : (
                    <XCircle className="h-5 w-5 text-rose-400" />
                  )}
                  <span className="font-mono text-sm font-bold text-white">
                    {ev.passed ? "ACCEPTED" : "FAILED"}
                  </span>
                </div>
                <div className="font-mono text-xs text-zinc-300">
                  {ev.elapsed_ms ? `${ev.elapsed_ms} ms` : ""}
                  {result?.xp_awarded > 0 ? ` · +${result.xp_awarded} XP` : ""}
                </div>
              </div>

              {/* Unit Tests Output */}
              {ev.tests && ev.tests.length > 0 && (
                <div className="space-y-1.5">
                  {ev.tests.map((t: any) => (
                    <div
                      key={t.name}
                      className="rounded border border-zinc-800 bg-zinc-950/80 px-3 py-2 font-mono text-xs"
                    >
                      <span className={t.passed ? "text-emerald-400" : "text-rose-400"}>
                        {t.passed ? "✓" : "✕"} {t.name}
                      </span>
                      {t.error && <p className="mt-1 text-rose-300">{t.error}</p>}
                    </div>
                  ))}
                </div>
              )}

              {/* Adversarial Puzzle Counterexamples */}
              {ev.counterexamples && ev.counterexamples.length > 0 && (
                <div className="space-y-2">
                  <p className="font-mono text-xs font-bold text-amber-300">
                    Adversarial Counterexamples That Broke Your Function:
                  </p>
                  {ev.counterexamples.map((cx: any, i: number) => (
                    <div
                      key={i}
                      className="rounded border border-amber-500/30 bg-zinc-950 p-3 font-mono text-xs space-y-1"
                    >
                      <p className="text-amber-300 font-bold">{cx.property}</p>
                      <p className="text-zinc-400">Input: {cx.input}</p>
                      <p className="text-rose-300">Your Output: {cx.your_output}</p>
                      <p className="text-zinc-200">{cx.why_broken}</p>
                    </div>
                  ))}
                </div>
              )}

              {/* Lab Metric */}
              {ev.details && <p className="font-mono text-xs text-zinc-200">{ev.details}</p>}

              {/* SymPy Math Results */}
              {ev.results && (
                <div className="space-y-1.5">
                  {ev.results.map((r: any) => (
                    <div
                      key={r.id}
                      className="rounded border border-zinc-800 bg-zinc-950 px-3 py-2 font-mono text-xs"
                    >
                      <span className={r.passed ? "text-emerald-400" : "text-rose-400"}>
                        {r.passed ? "✓" : "✕"} {r.id}: {r.feedback}
                      </span>
                      {r.hint && <p className="mt-1 text-amber-300">Hint: {r.hint}</p>}
                    </div>
                  ))}
                </div>
              )}

              {ev.stderr && (
                <pre className="overflow-x-auto rounded bg-zinc-950 p-2 font-mono text-xs text-rose-300">
                  {ev.stderr}
                </pre>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
