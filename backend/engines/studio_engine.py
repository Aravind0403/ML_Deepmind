"""Interview Studio Engine: JD/CV matching, Dual-Zone Stage 1, Gated 4-Stage Gauntlet & Prep Recap."""
from __future__ import annotations

import json
import re
import sqlite3
import uuid
from typing import Any

from backend.db import load_json, utc_now
from backend.engines.fsrs import update_fsrs_card
from backend.evaluators.llm_judge import judge_open_response
from backend.evaluators.runners import (
    evaluate_code_problem,
    evaluate_lab,
    evaluate_math_drills,
    evaluate_puzzle,
)

SKILL_KEYWORDS = {
    "linear-algebra": ["linear algebra", "matrix", "gemm", "tiling", "svd", "eigen"],
    "transformers": ["transformer", "attention", "causal", "rope", "positional", "llm"],
    "kv-cache": ["kv-cache", "kv cache", "paged", "pagedattention", "vllm", "fragmentation"],
    "roofline": ["roofline", "arithmetic intensity", "hbm", "bandwidth", "prefill", "decode", "ttft"],
    "speculative-decoding": ["speculative", "draft model", "rejection sampling"],
    "continuous-batching": ["continuous batching", "scheduler", "preemption", "serving", "throughput"],
    "quantization": ["quantization", "int8", "fp8", "nf4", "ptq", "gptq", "qlora"],
    "rlhf": ["rlhf", "dpo", "grpo", "ppo", "post-training", "reward", "reasoning"],
    "compilers": ["compiler", "mlir", "xla", "fusion", "ssa", "inductor", "kernel", "cuda", "triton"],
    "gnn": ["gnn", "graph neural", "message passing"],
    "continual-learning": ["continual", "forgetting", "ewc", "fisher"],
    "ai-safety": ["safety", "interpretability", "probe", "ablation", "alignment", "eval"],
    "mlops": ["mlops", "drift", "psi", "monitoring", "pipeline", "production"],
    "backprop": ["backprop", "mlp", "gradient", "regularization", "ridge"],
}

STAGE_PASS_THRESHOLD = 75.0


def extract_skills(text: str) -> list[str]:
    low = (text or "").lower()
    found = []
    for skill, kws in SKILL_KEYWORDS.items():
        if any(kw in low for kw in kws):
            found.append(skill)
    return found


def extract_cv_projects(cv_markdown: str, dossiers: dict[str, str]) -> list[dict[str, str]]:
    """Extract project headings from CV markdown and match with private War-Room Dossiers."""
    projects = []
    # Match '### 1. Project Name' or '### Project Name'
    blocks = re.split(r"(?m)^###\s+", cv_markdown or "")
    for blk in blocks[1:]:
        lines = [l.strip() for l in blk.splitlines() if l.strip()]
        if not lines:
            continue
        title = re.sub(r"^\d+\.\s*", "", lines[0]).strip()
        summary = "\n".join(lines[1:6])
        # Match best dossier by word overlap
        best_dossier = ""
        title_words = set(re.findall(r"[a-z0-9]+", title.lower()))
        best_score = 0
        for d_name, d_text in (dossiers or {}).items():
            d_words = set(re.findall(r"[a-z0-9]+", (d_name + " " + d_text[:300]).lower()))
            ov = len(title_words & d_words)
            if ov > best_score:
                best_score = ov
                best_dossier = d_text
        projects.append({"title": title, "summary": summary, "dossier": best_dossier})

    if not projects:
        projects.append(
            {
                "title": "Primary ML Systems Project from CV",
                "summary": (cv_markdown or "")[:400],
                "dossier": next(iter((dossiers or {}).values()), ""),
            }
        )
    return projects


def map_jd_cv_to_items(
    conn: sqlite3.Connection,
    jd_markdown: str,
    cv_markdown: str,
) -> tuple[list[str], list[str], list[str]]:
    """Return (jd_skills, cv_overlap_item_ids, jd_gap_item_ids)."""
    jd_skills = extract_skills(jd_markdown)
    cv_skills = set(extract_skills(cv_markdown))
    overlap_skills = [s for s in jd_skills if s in cv_skills]
    gap_skills = [s for s in jd_skills if s not in cv_skills]

    items = conn.execute("SELECT id, kind, title, difficulty, tags_json, unit_id FROM items ORDER BY sort_order").fetchall()

    def score_item(item_row, target_skills: list[str]) -> int:
        tags = set(load_json(item_row["tags_json"], []))
        title_low = item_row["title"].lower()
        hits = 0
        for sk in target_skills:
            if sk in tags or any(k in title_low for k in SKILL_KEYWORDS.get(sk, [])):
                hits += 1
        return hits

    overlap_scored = sorted(
        [(score_item(it, overlap_skills), it["id"]) for it in items if score_item(it, overlap_skills) > 0],
        key=lambda x: -x[0],
    )
    gap_scored = sorted(
        [(score_item(it, gap_skills), it["id"]) for it in items if score_item(it, gap_skills) > 0],
        key=lambda x: -x[0],
    )

    overlap_ids = [iid for _, iid in overlap_scored[:3]]
    gap_ids = [iid for _, iid in gap_scored if iid not in overlap_ids][:2]

    # Always guarantee at least 2 targeted items in Stage 1 even for sparse JDs
    if not overlap_ids:
        overlap_ids = [it["id"] for it in items[:2]]
    if not gap_ids:
        remaining = [it["id"] for it in items if it["id"] not in overlap_ids]
        gap_ids = remaining[:1]

    return jd_skills, overlap_ids, gap_ids


def create_studio_session(conn: sqlite3.Connection, target_id: str) -> dict[str, Any]:
    """Generate a personalized, gated 4-stage gauntlet for a target role."""
    target = conn.execute("SELECT * FROM target_roles WHERE id = ?", (target_id,)).fetchone()
    if not target:
        raise ValueError(f"Target role '{target_id}' not found")

    profile = conn.execute("SELECT * FROM user_profile WHERE id = 1").fetchone()
    cv_md = profile["cv_markdown"] if profile else ""
    dossiers = load_json(profile["dossiers_json"] if profile else "{}", {})
    star_md = profile["star_stories_markdown"] if profile else ""

    jd_skills, overlap_ids, gap_ids = map_jd_cv_to_items(conn, target["jd_markdown"], cv_md)
    conn.execute(
        "UPDATE target_roles SET parsed_skills_json = ?, cv_overlap_items_json = ?, jd_gap_items_json = ? WHERE id = ?",
        (json.dumps(jd_skills), json.dumps(overlap_ids), json.dumps(gap_ids), target_id),
    )

    # Pick a timed coding problem for Stage 2 (prefer hard/medium matching JD)
    all_coding = conn.execute(
        "SELECT id, title, difficulty, tags_json, payload_json FROM items WHERE kind = 'problem'"
    ).fetchall()
    stage2_coding = None
    for cid in overlap_ids + gap_ids:
        match = next((c for c in all_coding if c["id"] == cid), None)
        if match:
            stage2_coding = match
            break
    if stage2_coding is None and all_coding:
        stage2_coding = all_coding[0]

    # Dynamic timer by difficulty: easy=12m, medium=20m, hard=25m
    diff_timer_map = {"easy": 720, "medium": 1200, "hard": 1500}
    s2_time_sec = diff_timer_map.get(stage2_coding["difficulty"], 1200) if stage2_coding else 1200

    company = target["company"]
    role_title = target["role_title"]
    seniority = target["seniority"]
    primary_skill = jd_skills[0] if jd_skills else "inference"

    # Build Stage 2 System Design + Mid-Flight Constraint Shift + Deep Knowledge
    sd_prompt = (
        f"Design a production-scale {company} {role_title} architecture targeting `{', '.join(jd_skills[:4])}`. "
        "Include a Mermaid or ASCII architecture diagram, explicit HBM/FLOP/bandwidth back-of-the-envelope calculations, "
        "bottleneck analysis, and failure-mode mitigations."
    )
    sd_constraint_shift = (
        "MID-FLIGHT CONSTRAINT SHIFT (Staff Bar): Context length just jumped 10x (to 128k+ tokens) AND your HBM memory budget "
        "was cut by 40% while maintaining p99 TTFT SLA. Explicitly state what breaks first in your architecture and how you redesign it."
    )
    dk_prompt = (
        f"Staff Deep-Knowledge Edge-Case Probe ({company} — {role_title}): "
        f"Compare the exact mathematical & hardware failure modes across `{', '.join(jd_skills[:3])}`. "
        "When does your preferred optimization actually *regress* latency or accuracy, and how would you prove it with profiling or evals?"
    )

    # Build Stage 3 Project Deep-Dive anchored to CV + Private War-Room Dossier
    cv_projects = extract_cv_projects(cv_md, dossiers)
    top_proj = cv_projects[0]
    s3_questions = [
        {
            "id": "s3-arch",
            "title": f"Architecture & Rejected Alternatives — {top_proj['title']}",
            "prompt": (
                f"In your CV project '{top_proj['title']}', defend your core architectural choice against the two strongest alternatives you rejected. "
                "Cite concrete numbers (memory/latency/accuracy) from your implementation."
            ),
            "rubric_keywords": ["alternative", "trade-off", "latency", "memory", "hbm", "block", "throughput", "rejected"],
        },
        {
            "id": "s3-bottleneck",
            "title": f"Scaling Bottleneck & Production Failure — {top_proj['title']}",
            "prompt": (
                f"Walk through the worst scaling bottleneck or production failure mode you hit in '{top_proj['title']}'. "
                "How did you profile/diagnose it, and what happens if traffic or model size grows 10x?"
            ),
            "rubric_keywords": ["bottleneck", "profile", "p99", "oom", "preempt", "chunk", "scale", "failure"],
        },
    ]

    # Build Stage 4A (Managerial & Behavioral) AND Stage 4B (Research Vision & Taste — Silvia Sapora)
    s4_questions = [
        {
            "id": "s4-conflict",
            "title": f"{seniority}-Level Cross-Team Technical Conflict",
            "prompt": (
                f"Tell me about a time you pushed back on leadership or resolved a high-stakes disagreement between Research and Infrastructure teams "
                f"for a {seniority} scope decision. What objective evidence/RFC aligned everyone, and what trade-off did you own?"
            ),
            "rubric_keywords": ["rfc", "aligned", "trade-off", "metric", "team", "decision", "risk", "result"],
        },
        {
            "id": "s4-postmortem",
            "title": f"{seniority}-Level Ambiguity, Incident Ownership & Org Leverage",
            "prompt": (
                "Describe a high-severity silent degradation or ambiguous engineering problem where you owned the root cause and changed team-wide process "
                "so the entire class of failure could not recur."
            ),
            "rubric_keywords": ["root cause", "post-mortem", "monitor", "ci", "process", "prevent", "impact", "team"],
        },
    ]

    s4_research_questions = [
        {
            "id": "s4r-horizon",
            "title": f"Research Vision & 2-Year Field Trajectory ({company})",
            "prompt": (
                f"Where do you believe the highest-leverage bottleneck in `{', '.join(jd_skills[:3])}` will be in 2 years? "
                "Defend one contrarian research thesis where current industry consensus is missing a fundamental scaling limit."
            ),
            "rubric_keywords": ["bottleneck", "scaling", "hypothesis", "eval", "trade-off", "compute", "memory", "data"],
        },
        {
            "id": "s4r-day1-exp",
            "title": "Pitch a Falsifiable Day-1 Experiment & Ablation Plan",
            "prompt": (
                f"If you joined {company}'s {role_title} team Monday with a fixed compute budget, pitch one falsifiable experiment. "
                "Specify the baseline, exact ablation matrix, quantitative kill criteria, and what negative result would still teach the team something valuable."
            ),
            "rubric_keywords": ["baseline", "ablation", "metric", "compute", "falsifiable", "hypothesis", "kill", "variance"],
        },
    ]

    plan = {
        "target_id": target_id,
        "company": company,
        "role_title": role_title,
        "seniority": seniority,
        "jd_skills": jd_skills,
        "stage1": {
            "title": "Stage 1: Targeted JD/CV Syllabus (Non-Negotiable Baseline)",
            "track_1a_overlap_ids": overlap_ids,
            "track_1b_gap_ids": gap_ids,
        },
        "stage2": {
            "title": f"Stage 2: {seniority} Technical Gauntlet",
            "coding_item_id": stage2_coding["id"] if stage2_coding else None,
            "coding_time_limit_sec": s2_time_sec,
            "system_design": {
                "prompt": sd_prompt,
                "constraint_shift": sd_constraint_shift,
                "rubric_keywords": list(set(jd_skills + ["hbm", "latency", "throughput", "trade-off", "bottleneck", "batch", "memory", "scale"])),
            },
            "deep_knowledge": {
                "prompt": dk_prompt,
                "rubric_keywords": list(set(jd_skills + ["regress", "profile", "edge case", "variance", "bandwidth", "overhead", "trade-off"])),
            },
        },
        "stage3": {
            "title": "Stage 3: CV Project Deep-Dive (War-Room Defense)",
            "project_title": top_proj["title"],
            "project_summary": top_proj["summary"],
            "has_dossier": bool(top_proj["dossier"]),
            "dossier_excerpt": (top_proj["dossier"] or "")[:1200],
            "questions": s3_questions,
        },
        "stage4": {
            "title": f"Stage 4: Managerial & Behavioral / Research Vision ({seniority} Scope)",
            "has_star_bank": bool(star_md.strip()),
            "questions": s4_questions,
            "research_questions": s4_research_questions,
        },
    }

    stage_results = {
        "1": {"unlocked": True, "passed": False, "score": 0.0, "items": {}},
        "2": {"unlocked": False, "passed": False, "score": 0.0, "coding": None, "system_design": None, "deep_knowledge": None},
        "3": {"unlocked": False, "passed": False, "score": 0.0, "answers": {}},
        "4": {"unlocked": False, "passed": False, "score": 0.0, "answers": {}},
    }

    session_id = f"sess_{uuid.uuid4().hex[:10]}"
    conn.execute(
        """
        INSERT INTO studio_sessions (id, target_id, current_stage, status, plan_json, stage_results_json, started_at)
        VALUES (?, ?, 1, 'active', ?, ?, ?)
        """,
        (session_id, target_id, json.dumps(plan), json.dumps(stage_results), utc_now()),
    )
    conn.commit()
    return get_session_detail(conn, session_id)


def get_session_detail(conn: sqlite3.Connection, session_id: str) -> dict[str, Any]:
    row = conn.execute("SELECT * FROM studio_sessions WHERE id = ?", (session_id,)).fetchone()
    if not row:
        raise ValueError(f"Session '{session_id}' not found")
    plan = load_json(row["plan_json"], {})
    results = load_json(row["stage_results_json"], {})

    # Hydrate item metadata for Stage 1 and Stage 2 coding
    needed_ids = list(
        set(
            plan.get("stage1", {}).get("track_1a_overlap_ids", [])
            + plan.get("stage1", {}).get("track_1b_gap_ids", [])
            + ([plan.get("stage2", {}).get("coding_item_id")] if plan.get("stage2", {}).get("coding_item_id") else [])
        )
    )
    hydrated: dict[str, Any] = {}
    for iid in needed_ids:
        it = conn.execute("SELECT * FROM items WHERE id = ?", (iid,)).fetchone()
        if it:
            payload = load_json(it["payload_json"], {})
            hydrated[iid] = {
                "id": it["id"],
                "kind": it["kind"],
                "unit_id": it["unit_id"],
                "title": it["title"],
                "difficulty": it["difficulty"],
                "xp": it["xp"],
                "prompt_md": payload.get("prompt_md", ""),
                "worked_example_md": payload.get("worked_example_md", ""),
                "drills": payload.get("drills", []),
                "starter_code": payload.get("starter_code", ""),
            }

    return {
        "id": row["id"],
        "target_id": row["target_id"],
        "current_stage": row["current_stage"],
        "status": row["status"],
        "started_at": row["started_at"],
        "completed_at": row["completed_at"],
        "plan": plan,
        "stage_results": results,
        "hydrated_items": hydrated,
    }


def _save_session(
    conn: sqlite3.Connection,
    session_id: str,
    current_stage: int,
    status: str,
    stage_results: dict[str, Any],
    completed_at: str | None = None,
) -> None:
    conn.execute(
        """
        UPDATE studio_sessions
        SET current_stage = ?, status = ?, stage_results_json = ?, completed_at = COALESCE(?, completed_at)
        WHERE id = ?
        """,
        (current_stage, status, json.dumps(stage_results), completed_at, session_id),
    )
    conn.commit()


def submit_stage1_item(
    conn: sqlite3.Connection,
    session_id: str,
    item_id: str,
    code: str | None = None,
    math_answers: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Deterministically grade a Stage 1 non-negotiable baseline item; unlock Stage 2 when all pass."""
    sess = get_session_detail(conn, session_id)
    plan = sess["plan"]
    results = sess["stage_results"]
    req_ids = plan["stage1"]["track_1a_overlap_ids"] + plan["stage1"]["track_1b_gap_ids"]
    if item_id not in req_ids:
        raise ValueError(f"Item '{item_id}' is not part of Stage 1 for this session.")

    it = conn.execute("SELECT * FROM items WHERE id = ?", (item_id,)).fetchone()
    payload = load_json(it["payload_json"], {})
    kind = it["kind"]

    if kind == "math":
        eval_res = evaluate_math_drills(payload.get("drills", []), math_answers or {})
    elif kind == "puzzle":
        eval_res = evaluate_puzzle(code or "", payload.get("tests_code", ""))
    elif kind == "lab":
        eval_res = evaluate_lab(code or "", payload.get("tests_code", ""))
    else:
        eval_res = evaluate_code_problem(
            code or "",
            payload.get("tests_code", ""),
            banned_apis=payload.get("banned_apis", []),
            ban_matmul_op=bool(payload.get("ban_matmul_op", False)),
        )

    passed = bool(eval_res.get("passed"))
    score = 100.0 if passed else float(eval_res.get("score", 30.0))
    results["1"]["items"][item_id] = {
        "passed": passed,
        "score": score,
        "kind": kind,
        "title": it["title"],
        "unit_id": it["unit_id"],
        "failure_buckets": [] if passed else ["conceptual_gap", "implementation_friction"],
        "eval": eval_res,
    }

    if not passed:
        update_fsrs_card(conn, item_id, it["unit_id"], passed=False, studio_vulnerability=True)

    # Compute Stage 1 aggregate & unlock Stage 2 if all passed
    item_scores = [results["1"]["items"].get(rid, {}).get("score", 0.0) for rid in req_ids]
    all_passed = all(results["1"]["items"].get(rid, {}).get("passed", False) for rid in req_ids)
    results["1"]["score"] = round(sum(item_scores) / max(len(req_ids), 1), 1)
    results["1"]["passed"] = all_passed

    cur_stage = sess["current_stage"]
    if all_passed:
        results["2"]["unlocked"] = True
        cur_stage = max(cur_stage, 2)

    _save_session(conn, session_id, cur_stage, sess["status"], results)
    return {"evaluation": eval_res, "session": get_session_detail(conn, session_id)}


def submit_stage2(
    conn: sqlite3.Connection,
    session_id: str,
    coding_code: str,
    coding_duration_sec: int,
    system_design_answer: str,
    constraint_shift_answer: str,
    deep_knowledge_answer: str,
) -> dict[str, Any]:
    """Grade Stage 2 (Coding + System Design + Constraint Shift + Deep Knowledge). Strict gate from Stage 1."""
    sess = get_session_detail(conn, session_id)
    results = sess["stage_results"]
    if not results["2"]["unlocked"]:
        raise PermissionError("Stage 2 is locked. Complete and pass Stage 1 first.")

    plan2 = sess["plan"]["stage2"]
    cid = plan2["coding_item_id"]
    it = conn.execute("SELECT * FROM items WHERE id = ?", (cid,)).fetchone()
    payload = load_json(it["payload_json"], {})

    code_eval = evaluate_code_problem(
        coding_code or "",
        payload.get("tests_code", ""),
        banned_apis=payload.get("banned_apis", []),
        ban_matmul_op=bool(payload.get("ban_matmul_op", False)),
    )
    time_overrun = coding_duration_sec > int(plan2["coding_time_limit_sec"])
    coding_score = 100.0 if code_eval.get("passed") else 35.0
    if time_overrun:
        coding_score = max(0.0, coding_score - 15.0)
    coding_buckets = []
    if not code_eval.get("passed"):
        coding_buckets.append("implementation_friction")
    if time_overrun:
        coding_buckets.append("time_pressure_collapse")
    if not code_eval.get("passed"):
        update_fsrs_card(conn, cid, it["unit_id"], passed=False, studio_vulnerability=True)

    sd_combined = f"{system_design_answer}\n\n[Constraint Shift Defense]:\n{constraint_shift_answer}"
    sd_judge = judge_open_response(
        stage_label="Stage 2 — System Design + Constraint Shift",
        question=plan2["system_design"]["prompt"] + "\n" + plan2["system_design"]["constraint_shift"],
        answer=sd_combined,
        rubric_keywords=plan2["system_design"]["rubric_keywords"],
        context_notes=f"Target: {sess['plan']['company']} {sess['plan']['role_title']}",
        time_overrun=time_overrun,
    )
    dk_judge = judge_open_response(
        stage_label="Stage 2 — Staff Deep Knowledge",
        question=plan2["deep_knowledge"]["prompt"],
        answer=deep_knowledge_answer,
        rubric_keywords=plan2["deep_knowledge"]["rubric_keywords"],
        context_notes=f"Target: {sess['plan']['company']} {sess['plan']['role_title']}",
    )

    stage2_score = round(0.40 * coding_score + 0.35 * sd_judge["score"] + 0.25 * dk_judge["score"], 1)
    stage2_passed = bool(stage2_score >= STAGE_PASS_THRESHOLD and code_eval.get("passed"))

    results["2"]["coding"] = {
        "item_id": cid,
        "title": it["title"],
        "unit_id": it["unit_id"],
        "score": coding_score,
        "passed": bool(code_eval.get("passed")),
        "time_overrun": time_overrun,
        "duration_sec": coding_duration_sec,
        "failure_buckets": coding_buckets,
        "eval": code_eval,
    }
    results["2"]["system_design"] = sd_judge
    results["2"]["deep_knowledge"] = dk_judge
    results["2"]["score"] = stage2_score
    results["2"]["passed"] = stage2_passed

    cur_stage = sess["current_stage"]
    if stage2_passed:
        results["3"]["unlocked"] = True
        cur_stage = max(cur_stage, 3)

    _save_session(conn, session_id, cur_stage, sess["status"], results)
    return {"stage2": results["2"], "session": get_session_detail(conn, session_id)}


def submit_stage3(
    conn: sqlite3.Connection,
    session_id: str,
    answers: dict[str, str],
) -> dict[str, Any]:
    """Grade Stage 3 (CV Project Deep-Dive against private War-Room Dossier). Strict gate from Stage 2."""
    sess = get_session_detail(conn, session_id)
    results = sess["stage_results"]
    if not results["3"]["unlocked"]:
        raise PermissionError("Stage 3 is locked. Pass Stage 2 first.")

    plan3 = sess["plan"]["stage3"]
    dossier_ctx = f"Project: {plan3['project_title']}\nCV Summary: {plan3['project_summary']}\nWar-Room Dossier: {plan3['dossier_excerpt']}"

    scores = []
    for q in plan3["questions"]:
        qid = q["id"]
        judged = judge_open_response(
            stage_label=f"Stage 3 — {q['title']}",
            question=q["prompt"],
            answer=answers.get(qid, ""),
            rubric_keywords=q["rubric_keywords"],
            context_notes=dossier_ctx,
        )
        results["3"]["answers"][qid] = judged
        scores.append(judged["score"])

    stage3_score = round(sum(scores) / max(len(scores), 1), 1)
    stage3_passed = stage3_score >= STAGE_PASS_THRESHOLD
    results["3"]["score"] = stage3_score
    results["3"]["passed"] = stage3_passed

    cur_stage = sess["current_stage"]
    if stage3_passed:
        results["4"]["unlocked"] = True
        cur_stage = max(cur_stage, 4)

    _save_session(conn, session_id, cur_stage, sess["status"], results)
    return {"stage3": results["3"], "session": get_session_detail(conn, session_id)}


def submit_stage4(
    conn: sqlite3.Connection,
    session_id: str,
    answers: dict[str, str],
    track_mode: str = "behavioral",
) -> dict[str, Any]:
    """Grade Stage 4A (Managerial & Behavioral) or Stage 4B (Research Vision & Taste). Strict gate from Stage 3."""
    sess = get_session_detail(conn, session_id)
    results = sess["stage_results"]
    if not results["4"]["unlocked"]:
        raise PermissionError("Stage 4 is locked. Pass Stage 3 first.")

    plan4 = sess["plan"]["stage4"]
    q_list = (
        plan4.get("research_questions", plan4["questions"])
        if track_mode == "research_vision"
        else plan4["questions"]
    )
    scores = []
    for q in q_list:
        qid = q["id"]
        judged = judge_open_response(
            stage_label=f"Stage 4 ({track_mode}) — {q['title']}",
            question=q["prompt"],
            answer=answers.get(qid, ""),
            rubric_keywords=q["rubric_keywords"],
            context_notes=f"Seniority calibration: {sess['plan']['seniority']} at {sess['plan']['company']} ({track_mode})",
        )
        results["4"]["answers"][qid] = judged
        scores.append(judged["score"])

    stage4_score = round(sum(scores) / max(len(scores), 1), 1)
    stage4_passed = stage4_score >= STAGE_PASS_THRESHOLD
    results["4"]["track_mode"] = track_mode
    results["4"]["score"] = stage4_score
    results["4"]["passed"] = stage4_passed

    status = "completed" if stage4_passed else "active"
    completed_at = utc_now() if stage4_passed else None
    _save_session(conn, session_id, 4, status, results, completed_at=completed_at)
    return {"stage4": results["4"], "session": get_session_detail(conn, session_id)}


def abort_session(conn: sqlite3.Connection, session_id: str) -> dict[str, Any]:
    sess = get_session_detail(conn, session_id)
    _save_session(conn, session_id, sess["current_stage"], "aborted", sess["stage_results"], completed_at=utc_now())
    return build_recap(conn, session_id)


def build_recap(conn: sqlite3.Connection, session_id: str) -> dict[str, Any]:
    """Pillar 4 — Prep Recap: Strengths Heatmap, 5-Bucket Vulnerability Report, Targeted Remediation & Session Diff."""
    sess = get_session_detail(conn, session_id)
    res = sess["stage_results"]
    plan = sess["plan"]

    heatmap = [
        {"area": "Stage 1: JD/CV Baseline", "score": float(res["1"].get("score", 0.0)), "passed": bool(res["1"].get("passed"))},
        {"area": "Stage 2: Timed Coding", "score": float((res["2"].get("coding") or {}).get("score", 0.0)), "passed": bool((res["2"].get("coding") or {}).get("passed"))},
        {"area": "Stage 2: System Design", "score": float((res["2"].get("system_design") or {}).get("score", 0.0)), "passed": bool((res["2"].get("system_design") or {}).get("passed"))},
        {"area": "Stage 2: Deep Knowledge", "score": float((res["2"].get("deep_knowledge") or {}).get("score", 0.0)), "passed": bool((res["2"].get("deep_knowledge") or {}).get("passed"))},
        {"area": "Stage 3: Project Deep-Dive", "score": float(res["3"].get("score", 0.0)), "passed": bool(res["3"].get("passed"))},
        {"area": "Stage 4: Leadership & Behavioral", "score": float(res["4"].get("score", 0.0)), "passed": bool(res["4"].get("passed"))},
    ]

    bucket_counts = {
        "conceptual_gap": 0,
        "implementation_friction": 0,
        "complexity_bottleneck_blindness": 0,
        "communication_structuring": 0,
        "time_pressure_collapse": 0,
    }
    strengths: list[str] = []
    vulnerabilities: list[str] = []
    remediation_items: list[dict[str, Any]] = []
    seen_rem = set()

    def collect_judge(j: dict[str, Any] | None):
        if not j:
            return
        strengths.extend(j.get("strengths", []))
        vulnerabilities.extend(j.get("vulnerabilities", []))
        for b in j.get("failure_buckets", []):
            if b in bucket_counts:
                bucket_counts[b] += 1

    # Stage 1 telemetry
    for iid, data in (res["1"].get("items") or {}).items():
        if data.get("passed"):
            strengths.append(f"Passed Stage 1 baseline item: {data.get('title', iid)}")
        else:
            vulnerabilities.append(f"Stage 1 baseline failure on '{data.get('title', iid)}'")
            for b in data.get("failure_buckets", []):
                if b in bucket_counts:
                    bucket_counts[b] += 1
            if iid not in seen_rem:
                seen_rem.add(iid)
                remediation_items.append({"item_id": iid, "title": data.get("title", iid), "reason": "Failed Stage 1 non-negotiable baseline (3x FSRS boost applied)"})

    # Stage 2 telemetry
    c2 = res["2"].get("coding")
    if c2:
        if c2.get("passed") and not c2.get("time_overrun"):
            strengths.append(f"Passed Stage 2 timed coding '{c2['title']}' within time budget.")
        else:
            vulnerabilities.append(f"Stage 2 coding weakness on '{c2['title']}' (passed={c2.get('passed')}, time_overrun={c2.get('time_overrun')}).")
            for b in c2.get("failure_buckets", []):
                if b in bucket_counts:
                    bucket_counts[b] += 1
            if c2["item_id"] not in seen_rem:
                seen_rem.add(c2["item_id"])
                remediation_items.append({"item_id": c2["item_id"], "title": c2["title"], "reason": "Failed or timed out in Stage 2 Technical Gauntlet"})
    collect_judge(res["2"].get("system_design"))
    collect_judge(res["2"].get("deep_knowledge"))

    # Stage 3 & 4 telemetry
    for ans in (res["3"].get("answers") or {}).values():
        collect_judge(ans)
    for ans in (res["4"].get("answers") or {}).values():
        collect_judge(ans)

    # Always suggest JD gap items for remediation if vulnerabilities exist
    for gid in plan["stage1"].get("track_1b_gap_ids", []):
        if gid not in seen_rem and gid in sess["hydrated_items"]:
            seen_rem.add(gid)
            remediation_items.append(
                {
                    "item_id": gid,
                    "title": sess["hydrated_items"][gid]["title"],
                    "reason": "JD Blind-Spot Gap (JD \\ CV) — patch in Core Syllabus before next run",
                }
            )

    # Compute session diff vs previous session for same target
    prev = conn.execute(
        "SELECT id, stage_results_json FROM studio_sessions WHERE target_id = ? AND id != ? AND started_at < ? ORDER BY started_at DESC LIMIT 1",
        (sess["target_id"], session_id, sess["started_at"]),
    ).fetchone()
    diff_summary = None
    if prev:
        pr = load_json(prev["stage_results_json"], {})
        diff_summary = {
            "previous_session_id": prev["id"],
            "stage_deltas": {
                f"Stage {k}": round(float(res[k].get("score", 0.0)) - float(pr.get(k, {}).get("score", 0.0)), 1)
                for k in ("1", "2", "3", "4")
            },
        }

    return {
        "session_id": session_id,
        "target_id": sess["target_id"],
        "company": plan["company"],
        "role_title": plan["role_title"],
        "status": sess["status"],
        "current_stage": sess["current_stage"],
        "heatmap": heatmap,
        "failure_taxonomy": bucket_counts,
        "strengths": list(dict.fromkeys(strengths))[:8],
        "vulnerabilities": list(dict.fromkeys(vulnerabilities))[:8],
        "remediation": remediation_items,
        "session_diff": diff_summary,
    }
