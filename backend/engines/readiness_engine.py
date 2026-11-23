"""Pillar 5 — Readiness Score Engine: 3-Axis Delta, Veto Gates, Confidence Interval & Hiring Committee Memo."""
from __future__ import annotations

import math
import sqlite3
import uuid
from typing import Any

from backend.db import load_json, utc_now
from backend.engines.fsrs import compute_retrievability

TARGET_BAR = 85.0
VETO_FLOOR = 75.0


def compute_readiness_for_target(conn: sqlite3.Connection, target_id: str) -> dict[str, Any]:
    """Compute final Readiness Verdict. Strictly locked until at least one session completes all 4 stages."""
    target = conn.execute("SELECT * FROM target_roles WHERE id = ?", (target_id,)).fetchone()
    if not target:
        raise ValueError(f"Target role '{target_id}' not found")

    completed_sessions = conn.execute(
        """
        SELECT * FROM studio_sessions
        WHERE target_id = ? AND status = 'completed'
        ORDER BY completed_at DESC
        """,
        (target_id,),
    ).fetchall()

    if not completed_sessions:
        latest = conn.execute(
            "SELECT id, current_stage, status FROM studio_sessions WHERE target_id = ? ORDER BY started_at DESC LIMIT 1",
            (target_id,),
        ).fetchone()
        return {
            "unlocked": False,
            "target_id": target_id,
            "company": target["company"],
            "role_title": target["role_title"],
            "reason": "Readiness Score is strictly locked until all 4 Interview Studio stages are completed.",
            "latest_session_id": latest["id"] if latest else None,
            "latest_stage": latest["current_stage"] if latest else 0,
            "completed_runs": 0,
        }

    latest_completed = completed_sessions[0]
    res = load_json(latest_completed["stage_results_json"], {})
    plan = load_json(latest_completed["plan_json"], {})

    s1 = float(res["1"].get("score", 0.0))
    s2 = float(res["2"].get("score", 0.0))
    s3 = float(res["3"].get("score", 0.0))
    s4 = float(res["4"].get("score", 0.0))

    # 1. Execution Score (weighted: Stage 2 Technical Gauntlet carries highest weight for Senior/Staff)
    execution_score = round(0.15 * s1 + 0.40 * s2 + 0.25 * s3 + 0.20 * s4, 1)

    # 2. CV Fit (overlap ratio of JD skills already present on CV + dossier richness)
    jd_skills = load_json(target["parsed_skills_json"], [])
    overlap_ids = load_json(target["cv_overlap_items_json"], [])
    gap_ids = load_json(target["jd_gap_items_json"], [])
    profile = conn.execute("SELECT * FROM user_profile WHERE id = 1").fetchone()
    cv_low = (profile["cv_markdown"] if profile else "").lower()
    matched_skills = sum(1 for sk in jd_skills if sk.replace("-", " ") in cv_low or sk in cv_low)
    cv_base = 100.0 * matched_skills / max(len(jd_skills), 1)
    has_dossier = bool(plan.get("stage3", {}).get("has_dossier"))
    cv_fit = round(min(100.0, 0.80 * cv_base + (20.0 if has_dossier else 8.0)), 1)

    # 3. JD Coverage (Core Syllabus completion + FSRS effective decay on JD-relevant items)
    jd_item_ids = list(set(overlap_ids + gap_ids))
    effective_vals = []
    for iid in jd_item_ids:
        cp = conn.execute("SELECT status FROM core_progress WHERE item_id = ?", (iid,)).fetchone()
        fc = conn.execute("SELECT last_review_at, stability FROM fsrs_cards WHERE item_id = ?", (iid,)).fetchone()
        if cp and cp["status"] == "completed":
            r = compute_retrievability(fc["last_review_at"], fc["stability"]) if fc else 0.85
            effective_vals.append(max(0.65, r) * 100.0)
        elif res["1"].get("items", {}).get(iid, {}).get("passed"):
            effective_vals.append(85.0)
        else:
            effective_vals.append(25.0)
    jd_coverage = round(sum(effective_vals) / max(len(effective_vals), 1), 1)

    # Composite Readiness: Execution (60%) + JD Coverage (25%) + CV Fit (15%)
    composite = round(0.60 * execution_score + 0.25 * jd_coverage + 0.15 * cv_fit, 1)

    # Apply light time decay since latest completed Studio run
    run_decay = compute_retrievability(latest_completed["completed_at"], stability_days=14.0)
    effective_score = round(composite * (0.75 + 0.25 * run_decay), 1)

    # Per-Stage Hard Floor Veto Gates
    stage_scores = {
        "Stage 1 (JD/CV Baseline)": s1,
        "Stage 2 (Technical Gauntlet)": s2,
        "Stage 3 (Project Deep-Dive)": s3,
        "Stage 4 (Managerial & Behavioral)": s4,
    }
    veto_failures = [name for name, sc in stage_scores.items() if sc < VETO_FLOOR]
    veto_blocked_by = ", ".join(veto_failures) if veto_failures else None

    # Confidence interval shrinks with number of completed Studio runs (n=1 -> +-11%, n=4 -> +-5.5%)
    n_runs = len(completed_sessions)
    confidence_margin = round(11.0 / math.sqrt(n_runs), 1)

    # The Delta (distance from 85% Staff Interview Bar)
    delta_to_bar = round(effective_score - TARGET_BAR, 1)

    if veto_blocked_by:
        go_no_go = "NO-GO (VETO)"
        hc_decision = "Lean No-Hire"
    elif effective_score >= TARGET_BAR:
        go_no_go = "GO — SCHEDULE INTERVIEW"
        hc_decision = "Strong Hire" if effective_score >= 90.0 else "Hire"
    elif effective_score >= 75.0:
        go_no_go = "CONDITIONAL — PATCH GAPS"
        hc_decision = "Lean Hire / Borderline"
    else:
        go_no_go = "NO-GO — MORE PREP NEEDED"
        hc_decision = "No-Hire"

    weakest_stage = min(stage_scores.items(), key=lambda kv: kv[1])
    strongest_stage = max(stage_scores.items(), key=lambda kv: kv[1])
    level_cal = (
        f"{target['seniority']} (On-Level)"
        if effective_score >= 85.0 and not veto_blocked_by
        else f"Down-leveled ({target['seniority']} - 1)"
    )

    hc_memo = f"""### Simulated Hiring Committee Debrief — {target['company']} ({target['role_title']})

- **Committee Recommendation:** **{hc_decision}** | **Level Calibration:** `{level_cal}`
- **Go / No-Go Verdict:** `{go_no_go}` (**{effective_score:.1f}% ± {confidence_margin:.1f}%**, `n={n_runs}` completed loop{'s' if n_runs > 1 else ''})
- **Delta to {TARGET_BAR:.0f}% Bar:** `{delta_to_bar:+.1f}%`

#### Top Hiring Signals
1. Strongest performance in **{strongest_stage[0]}** (`{strongest_stage[1]:.1f}%`).
2. CV-to-JD alignment rated at **{cv_fit:.1f}%** across extracted role requirements (`{', '.join(jd_skills[:5])}`).

#### Primary Bar-Raiser Objection
- Weakest signal observed in **{weakest_stage[0]}** (`{weakest_stage[1]:.1f}%`). {"Hard veto gate triggered (< 75% floor) — a real Staff loop would likely reject or down-level despite strong scores elsewhere." if veto_blocked_by else "Recommend 1 additional timed simulation under tighter constraints to shrink confidence interval before scheduling."}
"""

    snap_id = f"snap_{uuid.uuid4().hex[:10]}"
    conn.execute(
        """
        INSERT INTO readiness_snapshots (
            id, target_id, session_id, composite_score, effective_score, cv_fit, jd_coverage,
            execution_score, delta_to_bar, veto_blocked_by, confidence_margin, go_no_go, hc_memo_markdown, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            snap_id,
            target_id,
            latest_completed["id"],
            composite,
            effective_score,
            cv_fit,
            jd_coverage,
            execution_score,
            delta_to_bar,
            veto_blocked_by,
            confidence_margin,
            go_no_go,
            hc_memo,
            utc_now(),
        ),
    )
    conn.commit()

    return {
        "unlocked": True,
        "snapshot_id": snap_id,
        "target_id": target_id,
        "company": target["company"],
        "role_title": target["role_title"],
        "seniority": target["seniority"],
        "latest_session_id": latest_completed["id"],
        "completed_runs": n_runs,
        "composite_score": composite,
        "effective_score": effective_score,
        "confidence_margin": confidence_margin,
        "target_bar": TARGET_BAR,
        "delta_to_bar": delta_to_bar,
        "axes": {
            "cv_fit": cv_fit,
            "jd_coverage": jd_coverage,
            "execution_score": execution_score,
        },
        "stage_scores": stage_scores,
        "veto_floor": VETO_FLOOR,
        "veto_blocked_by": veto_blocked_by,
        "go_no_go": go_no_go,
        "hc_decision": hc_decision,
        "level_calibration": level_cal,
        "hc_memo_markdown": hc_memo,
    }
