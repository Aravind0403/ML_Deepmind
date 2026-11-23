"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import {
  Swords,
  Plus,
  Trash2,
  Save,
  FileText,
  Shield,
  Award,
  BarChart3,
  Eye,
  Edit3,
  Layers,
  Sparkles,
  Info,
  CheckCircle2,
  FolderPlus,
} from "lucide-react";
import { apiFetch } from "@/lib/api";
import { MarkdownPreview } from "@/components/MarkdownPreview";

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

  // Vault Tab Navigation & Preview
  const [activeTab, setActiveTab] = useState<"cv" | "dossier" | "star">("cv");
  const [previewMode, setPreviewMode] = useState(false);
  const [dossierKey, setDossierKey] = useState("paged_inference_engine");
  const [showAddDossier, setShowAddDossier] = useState(false);
  const [newDossierSlug, setNewDossierSlug] = useState("");

  const loadAll = async () => {
    const [tRes, pRes] = await Promise.all([apiFetch("/api/targets"), apiFetch("/api/profile")]);
    setTargets(tRes.targets || []);
    setProfile(pRes);
    const keys = Object.keys(pRes.dossiers || {});
    if (keys.length > 0 && !pRes.dossiers[dossierKey]) {
      setDossierKey(keys[0]);
    }
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
      setTimeout(() => setProfileMsg(null), 4000);
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

  const addDossier = () => {
    const slug = newDossierSlug.trim().toLowerCase().replace(/[^a-z0-9_-]/g, "_");
    if (!slug || !profile) return;
    const updated = {
      ...profile.dossiers,
      [slug]: `# Project War-Room Dossier: ${newDossierSlug}\n\n- **Architecture:** \n- **Key Numbers & Metrics:** \n- **Rejected Alternatives:** \n- **Worst Scaling Bottleneck:** \n`,
    };
    setProfile({ ...profile, dossiers: updated });
    setDossierKey(slug);
    setNewDossierSlug("");
    setShowAddDossier(false);
  };

  const insertStarTemplate = (type: "conflict" | "outage" | "tradeoff") => {
    if (!profile) return;
    let template = "";
    if (type === "conflict") {
      template = `\n\n## Story: Resolving Cross-Team Serving Latency vs. Accuracy Trade-Off\n- **Situation:** Product team demanded a 128k context window globally; infra HBM was saturated at 16k.\n- **Task:** Ship extended context within 4 weeks without increasing GPU cluster spend by more than 10%.\n- **Action:** Authored an RFC comparing FP8 KV quantization, prefix caching, and chunked prefill; aligned Research & Infra teams on an empirical Pareto frontier.\n- **Result:** Decreased p99 TTFT by 2.1x and freed 38% HBM, allowing 64k context roll-out with zero regression in model accuracy.\n`;
    } else if (type === "outage") {
      template = `\n\n## Story: Silent Precision Loss & Gradient Degradation Incident\n- **Situation:** Distributed 70B training runs experienced silent loss spikes at step 4,200 with no OOM errors.\n- **Task:** Diagnose the root cause, save compute budget, and build guardrails so the failure cannot recur.\n- **Action:** Traced underflow to FP16 causal masking before softmax scaling; authored a custom Triton kernel with online scaling and automated CI numerical invariance tests.\n- **Result:** Saved ~$180k in compute by resuming from checkpoint; adopted the numerical verification harness across all distributed pipelines.\n`;
    } else if (type === "tradeoff") {
      template = `\n\n## Story: Staff Architecture Trade-Off & Technical RFC\n- **Situation:** New model family required low-latency streaming inference under strict bursty SLA.\n- **Task:** Propose and defend a serving architecture choice against senior leadership pushback.\n- **Action:** Evaluated PagedAttention vs. Contiguous buffers; designed a continuous batching prototype benchmark and presented the trade-off matrix.\n- **Result:** Aligned leadership on the proposed architecture; delivered 3.2x throughput gain under burst loads.\n`;
    }
    setProfile({
      ...profile,
      star_stories_markdown: (profile.star_stories_markdown || "") + template,
    });
  };

  const dossierList = Object.keys(profile?.dossiers || {});

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-wrap items-end justify-between gap-4 border-b border-zinc-800 pb-6">
        <div>
          <p className="font-mono text-xs uppercase tracking-widest text-emerald-400">
            Pillar 3 · Dynamic Hyper-Personalized Gauntlet
          </p>
          <h1 className="mt-1 text-2xl font-bold text-white sm:text-3xl">
            The Interview Studio & Private Vault
          </h1>
          <p className="mt-1 text-sm text-zinc-400">
            Configure your Target JDs, Master CV, Project War-Room Dossiers, and STAR stories. Launches a strictly calibrated 4-stage Staff gauntlet.
          </p>
        </div>
        <button
          type="button"
          onClick={() => setShowNew((v) => !v)}
          className="flex items-center gap-2 rounded-lg bg-emerald-600 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-500 shadow-sm transition"
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
                      className="text-zinc-600 hover:text-rose-400 transition"
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

      {/* Redesigned Private Local Vault with Full-Width Tabs & Formatted Preview */}
      {profile && (
        <section className="rounded-2xl border border-zinc-800 bg-zinc-900/40 p-6 space-y-6 shadow-xl">
          {/* Vault Header */}
          <div className="flex flex-wrap items-center justify-between gap-4 border-b border-zinc-800 pb-5">
            <div className="flex items-center gap-3">
              <div className="rounded-xl border border-emerald-500/30 bg-emerald-500/10 p-2.5 text-emerald-400">
                <Shield className="h-5 w-5" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h2 className="text-lg font-bold text-white">Private Local Vault</h2>
                  <span className="rounded-full bg-emerald-500/20 px-2.5 py-0.5 font-mono text-[10px] font-semibold text-emerald-300">
                    100% Offline SQLite
                  </span>
                </div>
                <p className="text-xs text-zinc-400 mt-0.5">
                  Your credentials and dossiers never leave your local database (<code>db/progress.sqlite</code>).
                </p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              {profileMsg && (
                <div className="flex items-center gap-1.5 text-xs text-emerald-300 font-medium">
                  <CheckCircle2 className="h-4 w-4" />
                  {profileMsg}
                </div>
              )}
              <button
                type="button"
                onClick={saveProfile}
                disabled={savingProfile}
                className="flex items-center gap-2 rounded-xl bg-emerald-600 px-5 py-2.5 text-xs font-semibold text-white hover:bg-emerald-500 shadow-md transition disabled:opacity-50"
              >
                <Save className="h-4 w-4" />
                {savingProfile ? "Saving & Re-Mapping..." : "Save & Re-Map JDs"}
              </button>
            </div>
          </div>

          {/* Navigation Tabs */}
          <div className="flex flex-wrap items-center justify-between gap-3 border-b border-zinc-800/80 pb-2">
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => setActiveTab("cv")}
                className={`flex items-center gap-2 rounded-xl px-4 py-2.5 text-xs font-semibold transition ${
                  activeTab === "cv"
                    ? "bg-zinc-800 text-white shadow-inner border border-zinc-700"
                    : "text-zinc-400 hover:bg-zinc-800/50 hover:text-zinc-200"
                }`}
              >
                <FileText className="h-4 w-4 text-sky-400" />
                <span>1. Master CV</span>
                <span className="rounded bg-sky-500/20 px-1.5 py-0.5 font-mono text-[10px] text-sky-300">
                  Stages 1 & 2
                </span>
              </button>

              <button
                type="button"
                onClick={() => setActiveTab("dossier")}
                className={`flex items-center gap-2 rounded-xl px-4 py-2.5 text-xs font-semibold transition ${
                  activeTab === "dossier"
                    ? "bg-zinc-800 text-white shadow-inner border border-zinc-700"
                    : "text-zinc-400 hover:bg-zinc-800/50 hover:text-zinc-200"
                }`}
              >
                <Layers className="h-4 w-4 text-amber-400" />
                <span>2. Project War-Room Dossiers</span>
                <span className="rounded bg-amber-500/20 px-1.5 py-0.5 font-mono text-[10px] text-amber-300">
                  Stage 3
                </span>
              </button>

              <button
                type="button"
                onClick={() => setActiveTab("star")}
                className={`flex items-center gap-2 rounded-xl px-4 py-2.5 text-xs font-semibold transition ${
                  activeTab === "star"
                    ? "bg-zinc-800 text-white shadow-inner border border-zinc-700"
                    : "text-zinc-400 hover:bg-zinc-800/50 hover:text-zinc-200"
                }`}
              >
                <Award className="h-4 w-4 text-purple-400" />
                <span>3. STAR Story Bank</span>
                <span className="rounded bg-purple-500/20 px-1.5 py-0.5 font-mono text-[10px] text-purple-300">
                  Stage 4
                </span>
              </button>
            </div>

            {/* Edit / Preview Toggle */}
            <div className="flex items-center gap-1 rounded-xl bg-zinc-950 p-1 border border-zinc-800">
              <button
                type="button"
                onClick={() => setPreviewMode(false)}
                className={`flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-medium transition ${
                  !previewMode ? "bg-zinc-800 text-white shadow-sm" : "text-zinc-400 hover:text-zinc-200"
                }`}
              >
                <Edit3 className="h-3.5 w-3.5" />
                <span>Editor</span>
              </button>
              <button
                type="button"
                onClick={() => setPreviewMode(true)}
                className={`flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-medium transition ${
                  previewMode ? "bg-zinc-800 text-white shadow-sm" : "text-zinc-400 hover:text-zinc-200"
                }`}
              >
                <Eye className="h-3.5 w-3.5" />
                <span>Formatted Preview</span>
              </button>
            </div>
          </div>

          {/* TAB 1: MASTER CV */}
          {activeTab === "cv" && (
            <div className="space-y-4">
              {/* Context Explanation Card */}
              <div className="rounded-xl border border-sky-500/30 bg-sky-950/20 p-4 text-xs text-sky-200 flex items-start gap-3">
                <Info className="h-4 w-4 text-sky-400 mt-0.5 shrink-0" />
                <div>
                  <strong className="font-semibold text-sky-100">How the AI Gauntlet uses your CV:</strong>
                  <p className="mt-1 text-sky-200/90 leading-relaxed">
                    When you add a Target Job Description, the engine cross-references this CV to find your{" "}
                    <strong>Skills Overlap</strong> (<code>CV ∩ JD</code>) and detects critical{" "}
                    <strong>Knowledge Gaps</strong> (<code>JD \ CV</code>). In Stage 2, it dynamically picks timed
                    coding problems and system design questions targeting your gaps.
                  </p>
                </div>
              </div>

              {previewMode ? (
                <MarkdownPreview content={profile.cv_markdown} />
              ) : (
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-xs text-zinc-400">
                    <span>Write or paste your markdown resume below.</span>
                    <span className="font-mono">{profile.cv_markdown?.length || 0} characters</span>
                  </div>
                  <textarea
                    rows={20}
                    value={profile.cv_markdown}
                    onChange={(e) => setProfile({ ...profile, cv_markdown: e.target.value })}
                    className="w-full rounded-xl border border-zinc-800 bg-zinc-950 p-4 font-mono text-xs text-zinc-100 focus:border-sky-500 focus:outline-none transition leading-relaxed"
                    placeholder="# Candidate CV&#10;&#10;## Summary&#10;...&#10;&#10;## Core Skills&#10;..."
                  />
                </div>
              )}
            </div>
          )}

          {/* TAB 2: PROJECT WAR-ROOM DOSSIERS */}
          {activeTab === "dossier" && (
            <div className="space-y-4">
              {/* Context Explanation Card */}
              <div className="rounded-xl border border-amber-500/30 bg-amber-950/20 p-4 text-xs text-amber-200 flex items-start gap-3">
                <Info className="h-4 w-4 text-amber-400 mt-0.5 shrink-0" />
                <div>
                  <strong className="font-semibold text-amber-100">Why Project War-Room Dossiers exist:</strong>
                  <p className="mt-1 text-amber-200/90 leading-relaxed">
                    In Staff & Principal ML interviews (Stage 3), interviewers grill you on the real-world truth
                    of your top projects: <em>rejected alternatives, exact HBM/latency numbers, and worst production scaling bottlenecks</em>.
                    The AI Bar-Raiser reads this dossier to challenge your claims.
                  </p>
                </div>
              </div>

              {/* Dossier Project Selector & Add Button */}
              <div className="flex flex-wrap items-center justify-between gap-3 bg-zinc-950/80 border border-zinc-800 p-3 rounded-xl">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="text-xs font-semibold text-zinc-400 uppercase tracking-wider font-mono mr-1">
                    Projects:
                  </span>
                  {dossierList.map((key) => (
                    <button
                      key={key}
                      type="button"
                      onClick={() => setDossierKey(key)}
                      className={`rounded-lg px-3 py-1.5 font-mono text-xs transition ${
                        dossierKey === key
                          ? "bg-amber-500/20 text-amber-300 border border-amber-500/40 font-bold"
                          : "bg-zinc-900 text-zinc-400 hover:text-zinc-200 border border-zinc-800"
                      }`}
                    >
                      {key}
                    </button>
                  ))}
                  <button
                    type="button"
                    onClick={() => setShowAddDossier((v) => !v)}
                    className="flex items-center gap-1 rounded-lg border border-dashed border-zinc-700 bg-zinc-900/50 px-3 py-1.5 text-xs text-zinc-400 hover:text-zinc-200 hover:border-zinc-500"
                  >
                    <FolderPlus className="h-3.5 w-3.5" />
                    <span>New Project</span>
                  </button>
                </div>

                <div className="text-xs font-mono text-zinc-400">
                  Editing: <span className="text-amber-400 font-semibold">{dossierKey}</span>
                </div>
              </div>

              {/* Add New Dossier Input */}
              {showAddDossier && (
                <div className="flex items-center gap-2 bg-zinc-900 p-3 rounded-xl border border-amber-500/40">
                  <input
                    placeholder="Project slug (e.g. grpo_post_training)"
                    value={newDossierSlug}
                    onChange={(e) => setNewDossierSlug(e.target.value)}
                    className="flex-1 rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-1.5 text-xs text-white font-mono"
                  />
                  <button
                    type="button"
                    onClick={addDossier}
                    className="rounded-lg bg-amber-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-amber-500"
                  >
                    Create Dossier
                  </button>
                  <button
                    type="button"
                    onClick={() => setShowAddDossier(false)}
                    className="rounded-lg border border-zinc-700 px-3 py-1.5 text-xs text-zinc-300"
                  >
                    Cancel
                  </button>
                </div>
              )}

              {previewMode ? (
                <MarkdownPreview content={(profile.dossiers || {})[dossierKey] || ""} />
              ) : (
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-xs text-zinc-400">
                    <span>Include architecture specs, exact latency/memory numbers, and rejected alternatives.</span>
                    <span className="font-mono">
                      {((profile.dossiers || {})[dossierKey] || "").length} characters
                    </span>
                  </div>
                  <textarea
                    rows={20}
                    value={(profile.dossiers || {})[dossierKey] || ""}
                    onChange={(e) =>
                      setProfile({
                        ...profile,
                        dossiers: { ...(profile.dossiers || {}), [dossierKey]: e.target.value },
                      })
                    }
                    className="w-full rounded-xl border border-zinc-800 bg-zinc-950 p-4 font-mono text-xs text-zinc-100 focus:border-amber-500 focus:outline-none transition leading-relaxed"
                    placeholder="# Project War-Room Dossier: [Project Name]&#10;&#10;- **Architecture:** ...&#10;- **Key Numbers:** ...&#10;- **Rejected Alternatives:** ...&#10;- **Worst Scaling Bottleneck:** ..."
                  />
                </div>
              )}
            </div>
          )}

          {/* TAB 3: STAR STORY BANK */}
          {activeTab === "star" && (
            <div className="space-y-4">
              {/* Context Explanation Card */}
              <div className="rounded-xl border border-purple-500/30 bg-purple-950/20 p-4 text-xs text-purple-200 flex items-start gap-3">
                <Info className="h-4 w-4 text-purple-400 mt-0.5 shrink-0" />
                <div>
                  <strong className="font-semibold text-purple-100">How Stage 4 tests your STAR Stories:</strong>
                  <p className="mt-1 text-purple-200/90 leading-relaxed">
                    Staff & Principal candidates are evaluated on <strong>organizational leverage</strong>, cross-team
                    technical conflict resolution, and handling production ambiguity. Format your stories as{" "}
                    <strong>Situation, Task, Action, Result</strong> with measurable impact.
                  </p>
                </div>
              </div>

              {/* Quick Template Chips */}
              {!previewMode && (
                <div className="flex flex-wrap items-center gap-2 bg-zinc-950/60 border border-zinc-800 p-2.5 rounded-xl">
                  <span className="text-xs font-semibold text-zinc-400 uppercase tracking-wider font-mono mr-1">
                    Quick Insert:
                  </span>
                  <button
                    type="button"
                    onClick={() => insertStarTemplate("conflict")}
                    className="flex items-center gap-1 rounded-lg border border-purple-500/30 bg-purple-500/10 px-2.5 py-1 text-xs text-purple-300 hover:bg-purple-500/20 transition"
                  >
                    <Sparkles className="h-3 w-3" />
                    + Conflict Resolution (Research vs. Infra)
                  </button>
                  <button
                    type="button"
                    onClick={() => insertStarTemplate("outage")}
                    className="flex items-center gap-1 rounded-lg border border-purple-500/30 bg-purple-500/10 px-2.5 py-1 text-xs text-purple-300 hover:bg-purple-500/20 transition"
                  >
                    <Sparkles className="h-3 w-3" />
                    + Incident Ownership & Root Cause
                  </button>
                  <button
                    type="button"
                    onClick={() => insertStarTemplate("tradeoff")}
                    className="flex items-center gap-1 rounded-lg border border-purple-500/30 bg-purple-500/10 px-2.5 py-1 text-xs text-purple-300 hover:bg-purple-500/20 transition"
                  >
                    <Sparkles className="h-3 w-3" />
                    + Architecture Trade-Off & RFC
                  </button>
                </div>
              )}

              {previewMode ? (
                <MarkdownPreview content={profile.star_stories_markdown} />
              ) : (
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-xs text-zinc-400">
                    <span>Write your STAR stories with explicit Situation, Task, Action, and Result bullets.</span>
                    <span className="font-mono">{profile.star_stories_markdown?.length || 0} characters</span>
                  </div>
                  <textarea
                    rows={20}
                    value={profile.star_stories_markdown}
                    onChange={(e) =>
                      setProfile({ ...profile, star_stories_markdown: e.target.value })
                    }
                    className="w-full rounded-xl border border-zinc-800 bg-zinc-950 p-4 font-mono text-xs text-zinc-100 focus:border-purple-500 focus:outline-none transition leading-relaxed"
                    placeholder="## Story 1: [Title]&#10;- **Situation:** ...&#10;- **Task:** ...&#10;- **Action:** ...&#10;- **Result:** ..."
                  />
                </div>
              )}
            </div>
          )}
        </section>
      )}
    </div>
  );
}
