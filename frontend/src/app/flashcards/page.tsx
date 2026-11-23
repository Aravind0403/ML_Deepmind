"use client";

import { useEffect, useState } from "react";
import { Layers, Plus, Save, RotateCw, CheckCircle2 } from "lucide-react";
import { apiFetch } from "@/lib/api";

export default function FlashcardsPage() {
  const [data, setData] = useState<any>(null);
  const [category, setCategory] = useState("All");
  const [onlyAuthored, setOnlyAuthored] = useState(false);
  const [selected, setSelected] = useState<any>(null);
  const [backDraft, setBackDraft] = useState("");
  const [flipped, setFlipped] = useState(false);
  const [saving, setSaving] = useState(false);

  const [showNew, setShowNew] = useState(false);
  const [newCat, setNewCat] = useState("LLMs");
  const [newTopic, setNewTopic] = useState("");
  const [newFront, setNewFront] = useState("");
  const [newBack, setNewBack] = useState("");

  const load = async (cat = category, authOnly = onlyAuthored) => {
    const q = new URLSearchParams();
    if (cat !== "All") q.set("category", cat);
    if (authOnly) q.set("only_authored", "true");
    const d = await apiFetch(`/api/flashcards?${q.toString()}`);
    setData(d);
    if (!selected && d.cards?.length > 0) {
      setSelected(d.cards[0]);
      setBackDraft(d.cards[0].user_back_markdown || "");
    }
  };

  useEffect(() => {
    load(category, onlyAuthored).catch(() => {});
  }, [category, onlyAuthored]);

  const selectCard = (c: any) => {
    setSelected(c);
    setBackDraft(c.user_back_markdown || "");
    setFlipped(false);
  };

  const saveCard = async () => {
    if (!selected) return;
    setSaving(true);
    try {
      await apiFetch(`/api/flashcards/${selected.id}`, {
        method: "PUT",
        body: JSON.stringify({ user_back_markdown: backDraft }),
      });
      await load();
      setSelected((prev: any) => ({ ...prev, user_back_markdown: backDraft, authored: !!backDraft.trim() }));
    } finally {
      setSaving(false);
    }
  };

  const gradeCard = async (rating: string) => {
    if (!selected) return;
    await apiFetch(`/api/flashcards/${selected.id}/review`, {
      method: "POST",
      body: JSON.stringify({ rating }),
    });
    setFlipped(false);
    await load();
  };

  const createCustom = async () => {
    if (!newTopic.trim() || !newFront.trim()) return;
    await apiFetch("/api/flashcards", {
      method: "POST",
      body: JSON.stringify({
        category: newCat,
        topic: newTopic,
        front_prompt: newFront,
        user_back_markdown: newBack,
      }),
    });
    setShowNew(false);
    setNewTopic("");
    setNewFront("");
    setNewBack("");
    await load();
  };

  if (!data) {
    return <div className="py-12 text-center font-mono text-sm text-zinc-500">Loading 115+ Frontier Flashcards...</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4 border-b border-zinc-800 pb-5">
        <div>
          <p className="font-mono text-xs uppercase tracking-widest text-amber-400">
            Phase 2 · Silvia Sapora Active-Recall Studio
          </p>
          <h1 className="mt-1 text-2xl font-bold text-white sm:text-3xl">
            Author-Your-Own FSRS Flashcards ({data.total} Frontier Topics)
          </h1>
          <p className="mt-1 text-sm text-zinc-400">
            Cards start intentionally blank so <em>writing your own first-principles explanation is half the learning</em>. Graded with FSRS memory decay.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div className="rounded-lg border border-zinc-800 bg-zinc-900 px-3 py-1.5 font-mono text-xs text-zinc-300">
            Authored: <strong className="text-emerald-400">{data.authored}/{data.total}</strong> · Due:{" "}
            <strong className="text-amber-400">{data.due}</strong>
          </div>
          <button
            type="button"
            onClick={() => setShowNew((v) => !v)}
            className="flex items-center gap-1.5 rounded-lg bg-emerald-600 px-3 py-2 text-xs font-semibold text-white hover:bg-emerald-500"
          >
            <Plus className="h-4 w-4" /> Custom Card
          </button>
        </div>
      </div>

      {showNew && (
        <div className="rounded-xl border border-emerald-500/40 bg-zinc-900 p-4 space-y-3">
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <select
              value={newCat}
              onChange={(e) => setNewCat(e.target.value)}
              className="rounded border border-zinc-700 bg-zinc-950 px-3 py-2 text-xs text-white"
            >
              {data.categories.map((c: string) => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>
            <input
              placeholder="Topic name (e.g. Ring Attention)"
              value={newTopic}
              onChange={(e) => setNewTopic(e.target.value)}
              className="rounded border border-zinc-700 bg-zinc-950 px-3 py-2 text-xs text-white"
            />
          </div>
          <input
            placeholder="Front prompt question..."
            value={newFront}
            onChange={(e) => setNewFront(e.target.value)}
            className="w-full rounded border border-zinc-700 bg-zinc-950 px-3 py-2 text-xs text-white"
          />
          <textarea
            rows={3}
            placeholder="Your own active-recall answer..."
            value={newBack}
            onChange={(e) => setNewBack(e.target.value)}
            className="w-full rounded border border-zinc-700 bg-zinc-950 p-2 font-mono text-xs text-white"
          />
          <button
            type="button"
            onClick={createCustom}
            className="rounded-lg bg-emerald-600 px-4 py-1.5 text-xs font-semibold text-white"
          >
            Save Custom Flashcard
          </button>
        </div>
      )}

      {/* Category Filter Bar */}
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex flex-wrap gap-1.5">
          {["All", ...data.categories].map((cat: string) => (
            <button
              key={cat}
              type="button"
              onClick={() => setCategory(cat)}
              className={`rounded-full border px-3 py-1 font-mono text-xs ${
                category === cat
                  ? "border-amber-400 bg-amber-500/20 text-amber-200 font-semibold"
                  : "border-zinc-800 bg-zinc-900 text-zinc-400 hover:text-white"
              }`}
            >
              {cat}
            </button>
          ))}
        </div>
        <label className="flex items-center gap-2 font-mono text-xs text-zinc-400 cursor-pointer">
          <input
            type="checkbox"
            checked={onlyAuthored}
            onChange={(e) => setOnlyAuthored(e.target.checked)}
            className="accent-emerald-500"
          />
          Show Authored Only
        </label>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Left Topic Index */}
        <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-3 space-y-1.5 max-h-[580px] overflow-y-auto">
          {data.cards.map((c: any) => (
            <button
              key={c.id}
              type="button"
              onClick={() => selectCard(c)}
              className={`flex w-full items-center justify-between gap-2 rounded-lg border px-3 py-2 text-left text-xs ${
                selected?.id === c.id
                  ? "border-amber-500 bg-amber-500/15 text-white"
                  : "border-zinc-900 bg-zinc-950/70 text-zinc-300 hover:border-zinc-700"
              }`}
            >
              <div className="min-w-0">
                <p className="truncate font-medium">{c.topic}</p>
                <p className="font-mono text-[10px] text-zinc-500">
                  {c.category} · {c.authored ? `S=${c.stability_days}d` : "Blank — write your own"}
                </p>
              </div>
              {c.authored && <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400 shrink-0" />}
            </button>
          ))}
        </div>

        {/* Right Authoring + FSRS Recall Workspace */}
        <div className="lg:col-span-2 rounded-xl border border-zinc-800 bg-zinc-900/60 p-6 space-y-5">
          {selected ? (
            <>
              <div className="flex items-center justify-between">
                <div>
                  <span className="font-mono text-xs uppercase text-amber-400">{selected.category}</span>
                  <h2 className="text-xl font-bold text-white">{selected.topic}</h2>
                </div>
                <button
                  type="button"
                  onClick={() => setFlipped((v) => !v)}
                  className="flex items-center gap-1.5 rounded-lg border border-zinc-700 bg-zinc-800 px-3 py-1.5 font-mono text-xs text-white hover:bg-zinc-700"
                >
                  <RotateCw className="h-3.5 w-3.5" /> {flipped ? "Edit Mode" : "Test Recall (Flip)"}
                </button>
              </div>

              <div className="rounded-lg border border-zinc-800 bg-zinc-950 p-4">
                <p className="font-mono text-[11px] uppercase text-zinc-500 mb-1">Front Prompt</p>
                <p className="text-sm text-zinc-100">{selected.front_prompt}</p>
              </div>

              {!flipped ? (
                <div className="space-y-3">
                  <label className="font-mono text-xs uppercase text-emerald-400">
                    Your Own Active-Recall Note (Equations, Failure Modes, Interview One-Liner)
                  </label>
                  <textarea
                    rows={9}
                    value={backDraft}
                    onChange={(e) => setBackDraft(e.target.value)}
                    placeholder="Write from memory first, then verify against papers/docs. Include key equations, complexity/HBM trade-offs, and one common Staff interview trap..."
                    className="w-full rounded-lg border border-zinc-700 bg-zinc-950 p-3 font-mono text-xs text-zinc-100"
                  />
                  <button
                    type="button"
                    onClick={saveCard}
                    disabled={saving}
                    className="flex items-center gap-1.5 rounded-lg bg-emerald-600 px-4 py-2 text-xs font-semibold text-white hover:bg-emerald-500"
                  >
                    <Save className="h-3.5 w-3.5" />
                    {saving ? "Saving..." : "Save Card & Enroll in FSRS"}
                  </button>
                </div>
              ) : (
                <div className="space-y-4">
                  <div className="rounded-lg border border-emerald-500/30 bg-emerald-500/5 p-4">
                    <p className="font-mono text-[11px] uppercase text-emerald-400 mb-2">
                      Your Authored Answer
                    </p>
                    <pre className="whitespace-pre-wrap font-mono text-xs text-zinc-200">
                      {selected.user_back_markdown || "You haven't written this card yet — switch to Edit Mode to author it!"}
                    </pre>
                  </div>
                  <div className="space-y-2">
                    <p className="font-mono text-xs text-zinc-400">Grade your recall (updates FSRS stability):</p>
                    <div className="grid grid-cols-4 gap-2">
                      {[
                        { r: "again", label: "Again (Reset)", cls: "border-rose-500/50 bg-rose-500/15 text-rose-200" },
                        { r: "hard", label: "Hard", cls: "border-amber-500/50 bg-amber-500/15 text-amber-200" },
                        { r: "good", label: "Good", cls: "border-emerald-500/50 bg-emerald-500/15 text-emerald-200" },
                        { r: "easy", label: "Easy", cls: "border-sky-500/50 bg-sky-500/15 text-sky-200" },
                      ].map((btn) => (
                        <button
                          key={btn.r}
                          type="button"
                          onClick={() => gradeCard(btn.r)}
                          className={`rounded-lg border py-2 font-mono text-xs font-semibold hover:opacity-90 ${btn.cls}`}
                        >
                          {btn.label}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </>
          ) : (
            <div className="flex items-center gap-2 text-sm text-zinc-500">
              <Layers className="h-4 w-4" /> Select a topic from the left checklist.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
