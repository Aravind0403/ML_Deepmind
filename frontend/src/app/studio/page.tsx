"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Swords, Plus, Trash2, Save, FileText, Shield, Award, BarChart3 } from "lucide-react";
import { apiFetch } from "@/lib/api";

export default function StudioHubPage() {
  const [targets, setTargets] = useState<any[]>([]);
  const [profile, setProfile] = useState<any>(null);
  const [savingProfile, setSavingProfile] = useState(false);
  const [profileMsg, setProfileMsg] = useState<string | null>(null);

  const [showNew, setShowNew] = useState(false);
  const [company, setCompany] = useState("");
  const [roleTitle, setRoleTitle] = useState("");
  const [seniority, setSeniority] = useState("Staff");
  const [targetDate, setTargetDate] = useState("2027-01-15");
  const [jdMarkdown, setJdMarkdown] = useState("");

  const [dossierKey, setDossierKey] = useState("paged_inference_engine");

  const loadAll = async () => {
    const [tRes, pRes] = await Promise.all([apiFetch("/api/targets"), apiFetch("/api/profile")]);
    setTargets(tRes.targets || []);
    setProfile(pRes);
    const keys = Object.keys(pRes.dossiers || {});
    if (keys.length > 0 && !pRes.dossiers[dossierKey]) setDossierKey(keys[0]);
  };

  useEffect(() => {
    loadAll().catch(() => {});
  }, []);

  const saveProfile = async () => {
    if (!profile) return;
    setSavingProfile(true);
    setProfileMsg(null);
    try {
      await apiFetch("/api/profile", {
        method: "PUT",
        body: JSON.stringify({
          cv_markdown: profile.cv_markdown,
          star_stories_markdown: profile.star_stories_markdown,
          dossiers: profile.dossiers,
        }),
      });
      setProfileMsg("Saved privately to local SQLite & re-mapped all Target JDs.");
      await loadAll();
    } finally {
      setSavingProfile(false);
    }
  };

  const addTarget = async () => {
    if (!company.trim() || !roleTitle.trim() || !jdMarkdown.trim()) return;
    await apiFetch("/api/targets", {
      method: "POST",
      body: JSON.stringify({
        company,
        role_title: roleTitle,
        seniority,
        target_date: targetDate || null,
        jd_markdown: jdMarkdown,
      }),
    });
    setShowNew(false);
    setCompany("");
    setRoleTitle("");
    setJdMarkdown("");
    await loadAll();
  };

  const removeTarget = async (id: string) => {
    await apiFetch(`/api/targets/${id}`, { method: "DELETE" });
    await loadAll();
  };

  return (
    <div className="space-y-8">
      <div className="flex flex-wrap items-end justify-between gap-4 border-b border-zinc-800 pb-6">
        <div>
          <p className="font-mono text-xs uppercase tracking-widest text-emerald-400">
            Pillar 3 · Dynamic Hyper-Personalized Gauntlet
          </p>
          <h1 className="mt-1 text-2xl font-bold text-white sm:text-3xl">
            The Interview Studio & Private Vault
          </h1>
          <p className="mt-1 text-sm text-zinc-400">
            Input your Target JD, real CV, and Project War-Room Dossiers locally. Launches a strictly gated 4-stage Staff gauntlet.
          </p>
        </div>
        <button
          type="button"
          onClick={() => setShowNew((v) => !v)}
          className="flex items-center gap-2 rounded-lg bg-emerald-600 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-500"
        >
          <Plus className="h-4 w-4" /> New Target JD Pipeline
        </button>
      </div>

      {/* Add New Target JD Form */}
      {showNew && (
        <div className="rounded-xl border border-emerald-500/40 bg-zinc-900 p-5 space-y-4">
          <h2 className="text-sm font-semibold text-white">Add Target Company & Role JD</h2>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-4">
            <input
              placeholder="Company (e.g. OpenAI)"
              value={company}
              onChange={(e) => setCompany(e.target.value)}
              className="rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm text-white"
            />
            <input
              placeholder="Role (e.g. Inference Research)"
              value={roleTitle}
              onChange={(e) => setRoleTitle(e.target.value)}
              className="rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm text-white"
            />
            <select
              value={seniority}
              onChange={(e) => setSeniority(e.target.value)}
              className="rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm text-white"
            >
              <option value="Senior">Senior</option>
              <option value="Senior/Staff">Senior/Staff</option>
              <option value="Staff">Staff</option>
              <option value="Principal">Principal</option>
            </select>
            <input
              type="date"
              value={targetDate}
              onChange={(e) => setTargetDate(e.target.value)}
              className="rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm text-white"
            />
          </div>
          <textarea
            rows={5}
            placeholder="Paste full Job Description here (skills like KV-cache, Roofline, Triton, Quantization, GRPO, Compilers, Safety are auto-mapped against your CV)..."
            value={jdMarkdown}
            onChange={(e) => setJdMarkdown(e.target.value)}
            className="w-full rounded-lg border border-zinc-700 bg-zinc-950 p-3 font-mono text-xs text-zinc-100"
          />
          <div className="flex justify-end gap-2">
            <button
              type="button"
              onClick={() => setShowNew(false)}
              className="rounded-lg border border-zinc-700 px-3 py-1.5 text-xs text-zinc-300"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={addTarget}
              className="rounded-lg bg-emerald-600 px-4 py-1.5 text-xs font-semibold text-white hover:bg-emerald-500"
            >
              Create Pipeline & Parse JD
            </button>
          </div>
        </div>
      )}

      {/* Target Pipelines */}
      <section className="space-y-3">
        <h2 className="text-lg font-semibold text-white">Target Role Pipelines ({targets.length})</h2>
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
          {targets.map((t) => {
            const latest = t.sessions?.[0];
            return (
              <div
                key={t.id}
                className="flex flex-col justify-between rounded-xl border border-zinc-800 bg-zinc-900/60 p-5 space-y-4"
              >
                <div className="space-y-3">
                  <div className="flex items-start justify-between">
                    <div>
                      <span className="font-mono text-xs font-bold uppercase text-emerald-400">
                        {t.company} · {t.seniority}
                      </span>
                      <h3 className="text-base font-bold text-white">{t.role_title}</h3>
                    </div>
                    <button
                      type="button"
                      onClick={() => removeTarget(t.id)}
                      className="text-zinc-600 hover:text-rose-400"
                      title="Delete target"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>

                  <div className="space-y-1.5 text-xs">
                    <p className="font-mono text-[11px] text-zinc-400">
                      Track 1A (CV ∩ JD):{" "}
                      <span className="text-sky-300">{t.cv_overlap_items?.length || 0} baseline items</span>
                    </p>
                    <p className="font-mono text-[11px] text-zinc-400">
                      Track 1B (JD \ CV Gaps):{" "}
                      <span className="text-amber-300">{t.jd_gap_items?.length || 0} gap items</span>
                    </p>
                  </div>

                  <div className="flex flex-wrap gap-1">
                    {(t.parsed_skills || []).map((s: string) => (
                      <span
                        key={s}
                        className="rounded bg-zinc-950 border border-zinc-800 px-1.5 py-0.5 font-mono text-[10px] text-zinc-400"
                      >
                        {s}
                      </span>
                    ))}
                  </div>
                </div>

                <div className="space-y-2 border-t border-zinc-800 pt-3">
                  <Link
                    href={`/studio/${t.id}`}
                    className="flex w-full items-center justify-center gap-2 rounded-lg bg-emerald-600 px-3 py-2 text-xs font-semibold text-white hover:bg-emerald-500"
                  >
                    <Swords className="h-3.5 w-3.5" />
                    {latest ? `Open Gauntlet (Stage ${latest.current_stage}/4 · ${latest.status})` : "Start 4-Stage Gauntlet"}
                  </Link>
                  <div className="grid grid-cols-2 gap-2">
                    {latest ? (
                      <Link
                        href={`/recap/${latest.id}`}
                        className="flex items-center justify-center gap-1 rounded-lg border border-zinc-700 bg-zinc-950 py-1.5 font-mono text-[11px] text-zinc-300 hover:bg-zinc-800"
                      >
                        <BarChart3 className="h-3 w-3" /> Prep Recap
                      </Link>
                    ) : (
                      <span className="flex items-center justify-center rounded-lg border border-zinc-900 py-1.5 font-mono text-[11px] text-zinc-600">
                        No Recap Yet
                      </span>
                    )}
                    <Link
                      href={`/readiness/${t.id}`}
                      className="flex items-center justify-center gap-1 rounded-lg border border-zinc-700 bg-zinc-950 py-1.5 font-mono text-[11px] text-emerald-300 hover:bg-zinc-800"
                    >
                      <Award className="h-3 w-3" /> Readiness
                    </Link>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </section>

      {/* Private Local Vault: CV, War-Room Dossiers & STAR Stories */}
      {profile && (
        <section className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-6 space-y-5">
          <div className="flex flex-wrap items-center justify-between gap-2 border-b border-zinc-800 pb-3">
            <div className="flex items-center gap-2">
              <Shield className="h-5 w-5 text-emerald-400" />
              <div>
                <h2 className="text-base font-bold text-white">
                  Private Local Vault (CV, Project War-Room Dossiers & STAR Bank)
                </h2>
                <p className="text-xs text-zinc-400">
                  Stored strictly in local SQLite (<code>db/progress.sqlite</code>, gitignored). Drives Stage 1 matching, Stage 3 deep-dive interrogation, and Stage 4 scope calibration.
                </p>
              </div>
            </div>
            <button
              type="button"
              onClick={saveProfile}
              disabled={savingProfile}
              className="flex items-center gap-1.5 rounded-lg bg-sky-600 px-4 py-2 text-xs font-semibold text-white hover:bg-sky-500 disabled:opacity-50"
            >
              <Save className="h-3.5 w-3.5" />
              {savingProfile ? "Saving..." : "Save & Re-Map JDs"}
            </button>
          </div>

          {profileMsg && (
            <div className="rounded-lg border border-emerald-500/40 bg-emerald-500/10 px-3 py-2 text-xs text-emerald-200">
              {profileMsg}
            </div>
          )}

          <div className="grid grid-cols-1 gap-5 lg:grid-cols-3">
            <div className="space-y-2">
              <label className="flex items-center gap-1.5 font-mono text-xs font-bold uppercase text-zinc-300">
                <FileText className="h-3.5 w-3.5 text-sky-400" /> Your CV (Markdown)
              </label>
              <textarea
                rows={12}
                value={profile.cv_markdown}
                onChange={(e) => setProfile({ ...profile, cv_markdown: e.target.value })}
                className="w-full rounded-lg border border-zinc-800 bg-zinc-950 p-3 font-mono text-xs text-zinc-200"
              />
            </div>

            <div className="space-y-2">
              <label className="flex items-center justify-between font-mono text-xs font-bold uppercase text-zinc-300">
                <span>Project War-Room Dossier (Stage 3)</span>
                <span className="text-[10px] text-amber-400">{dossierKey}</span>
              </label>
              <textarea
                rows={12}
                value={(profile.dossiers || {})[dossierKey] || ""}
                onChange={(e) =>
                  setProfile({
                    ...profile,
                    dossiers: { ...(profile.dossiers || {}), [dossierKey]: e.target.value },
                  })
                }
                className="w-full rounded-lg border border-zinc-800 bg-zinc-950 p-3 font-mono text-xs text-zinc-200"
              />
            </div>

            <div className="space-y-2">
              <label className="font-mono text-xs font-bold uppercase text-zinc-300">
                STAR Story Bank (Stage 4)
              </label>
              <textarea
                rows={12}
                value={profile.star_stories_markdown}
                onChange={(e) =>
                  setProfile({ ...profile, star_stories_markdown: e.target.value })
                }
                className="w-full rounded-lg border border-zinc-800 bg-zinc-950 p-3 font-mono text-xs text-zinc-200"
              />
            </div>
          </div>
        </section>
      )}
    </div>
  );
}
