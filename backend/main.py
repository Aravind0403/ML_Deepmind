"""FastAPI server for the Private ML Deep-Path & Interview Studio Command Center."""
from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.db import get_conn, init_db, load_json, utc_now
from backend.engines.flashcards_engine import list_flashcards, review_flashcard, seed_frontier_flashcards
from backend.engines.fsrs import (
    acknowledge_review_checkpoint,
    compute_retrievability,
    get_review_status,
    update_fsrs_card,
)
from backend.engines.readiness_engine import compute_readiness_for_target
from backend.engines.studio_engine import (
    abort_session,
    build_recap,
    create_studio_session,
    get_session_detail,
    map_jd_cv_to_items,
    submit_stage1_item,
    submit_stage2,
    submit_stage3,
    submit_stage4,
)
from backend.evaluators.runners import (
    evaluate_code_problem,
    evaluate_lab,
    evaluate_math_drills,
    evaluate_puzzle,
)

init_db()

app = FastAPI(title="ML Deep-Path & Interview Studio API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ------------------------------------------------------------------
# Request Models
# ------------------------------------------------------------------
class EvaluateItemRequest(BaseModel):
    code: str | None = None
    math_answers: dict[str, str] | None = None
    is_review: bool = False


class PlacementSubmitRequest(BaseModel):
    answer: str


class ProfileUpdateRequest(BaseModel):
    cv_markdown: str
    star_stories_markdown: str
    dossiers: dict[str, str]


class CreateTargetRequest(BaseModel):
    company: str
    role_title: str
    seniority: str = "Staff"
    target_date: str | None = None
    jd_markdown: str


class CreateSessionRequest(BaseModel):
    target_id: str


class Stage1SubmitRequest(BaseModel):
    code: str | None = None
    math_answers: dict[str, str] | None = None


class Stage2SubmitRequest(BaseModel):
    coding_code: str
    coding_duration_sec: int = 600
    system_design_answer: str
    constraint_shift_answer: str
    deep_knowledge_answer: str


class Stage3SubmitRequest(BaseModel):
    answers: dict[str, str]


class Stage4SubmitRequest(BaseModel):
    answers: dict[str, str]
    track_mode: str = "behavioral"  # behavioral | research_vision


class ItemNotesRequest(BaseModel):
    expected_text: str = ""
    observed_text: str = ""
    why_text: str = ""


class CreateFlashcardRequest(BaseModel):
    category: str
    topic: str
    front_prompt: str
    user_back_markdown: str = ""


class UpdateFlashcardRequest(BaseModel):
    user_back_markdown: str
    front_prompt: str | None = None


class ReviewFlashcardRequest(BaseModel):
    rating: str  # again | hard | good | easy


class CrmUpdateRequest(BaseModel):
    app_stage: str = "Researching"
    referral_contact: str = ""
    cold_email_draft: str = ""
    interview_dates: list[str] = []
    offer: dict[str, Any] = {}


# ------------------------------------------------------------------
# Pillar 1: Overview Dashboard
# ------------------------------------------------------------------
@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/overview")
def get_overview():
    conn = get_conn()
    try:
        tracks = conn.execute("SELECT * FROM tracks ORDER BY sort_order").fetchall()
        track_stats = []
        total_items_all = 0
        total_done_all = 0

        for tr in tracks:
            items = conn.execute(
                """
                SELECT i.id, cp.status, fc.last_review_at, fc.stability
                FROM items i
                JOIN units u ON u.id = i.unit_id
                LEFT JOIN core_progress cp ON cp.item_id = i.id
                LEFT JOIN fsrs_cards fc ON fc.item_id = i.id
                WHERE u.track_id = ?
                """,
                (tr["id"],),
            ).fetchall()
            n_total = len(items)
            n_done = sum(1 for it in items if it["status"] == "completed")
            total_items_all += n_total
            total_done_all += n_done

            peak_pct = round(100.0 * n_done / max(n_total, 1), 1)
            eff_sum = 0.0
            for it in items:
                if it["status"] == "completed":
                    r = compute_retrievability(it["last_review_at"], it["stability"] or 4.0)
                    eff_sum += max(0.55, r)
            effective_pct = round(100.0 * eff_sum / max(n_total, 1), 1)

            track_stats.append(
                {
                    "id": tr["id"],
                    "title": tr["title"],
                    "subtitle": tr["subtitle"],
                    "color": tr["color"],
                    "completed": n_done,
                    "total": n_total,
                    "peak_pct": peak_pct,
                    "effective_pct": effective_pct,
                }
            )

        # Target Company Pipelines driven by Interview Studio performance
        targets = conn.execute("SELECT * FROM target_roles ORDER BY created_at ASC").fetchall()
        pipelines = []
        now_dt = datetime.now(timezone.utc)
        for t in targets:
            latest_sess = conn.execute(
                "SELECT * FROM studio_sessions WHERE target_id = ? ORDER BY started_at DESC LIMIT 1",
                (t["id"],),
            ).fetchone()
            latest_snap = conn.execute(
                "SELECT * FROM readiness_snapshots WHERE target_id = ? ORDER BY created_at DESC LIMIT 1",
                (t["id"],),
            ).fetchone()

            # Dynamic readiness bar: full snapshot if unlocked, else partial stage progress in Interview Studio
            if latest_snap:
                prepared_pct = float(latest_snap["effective_score"])
                go_no_go = latest_snap["go_no_go"]
                readiness_unlocked = True
            elif latest_sess:
                sr = load_json(latest_sess["stage_results_json"], {})
                avg_stage = (
                    float(sr["1"].get("score", 0)) * 0.15
                    + float(sr["2"].get("score", 0)) * 0.40
                    + float(sr["3"].get("score", 0)) * 0.25
                    + float(sr["4"].get("score", 0)) * 0.20
                )
                prepared_pct = round(avg_stage * 0.75, 1)
                go_no_go = f"IN STUDIO (STAGE {latest_sess['current_stage']}/4)"
                readiness_unlocked = False
            else:
                prepared_pct = 0.0
                go_no_go = "NOT STARTED"
                readiness_unlocked = False

            days_left = None
            pacing_status = "UNSCHEDULED"
            daily_hours_needed = None
            if t["target_date"]:
                try:
                    tdt = datetime.fromisoformat(t["target_date"]).replace(tzinfo=timezone.utc)
                    days_left = max(0, (tdt - now_dt).days)
                    gap = max(0.0, 85.0 - prepared_pct)
                    if days_left == 0:
                        pacing_status = "ON TRACK" if prepared_pct >= 85.0 else "AT RISK"
                        daily_hours_needed = round(gap / 10.0, 1)
                    else:
                        # Rough model: ~0.4 hrs per readiness percentage point
                        daily_hours_needed = round((gap * 0.4) / max(days_left, 1), 1)
                        pacing_status = "ON TRACK" if daily_hours_needed <= 2.0 else ("AT RISK" if daily_hours_needed <= 4.0 else "OVER-SCOPED")
                except Exception:
                    pass

            pipelines.append(
                {
                    "id": t["id"],
                    "company": t["company"],
                    "role_title": t["role_title"],
                    "seniority": t["seniority"],
                    "target_date": t["target_date"],
                    "days_left": days_left,
                    "daily_hours_needed": daily_hours_needed,
                    "pacing_status": pacing_status,
                    "prepared_pct": prepared_pct,
                    "go_no_go": go_no_go,
                    "readiness_unlocked": readiness_unlocked,
                    "latest_session_id": latest_sess["id"] if latest_sess else None,
                    "latest_session_stage": latest_sess["current_stage"] if latest_sess else 0,
                    "latest_session_status": latest_sess["status"] if latest_sess else None,
                    "parsed_skills": load_json(t["parsed_skills_json"], []),
                }
            )

        review = get_review_status(conn)
        return {
            "core_summary": {
                "completed": total_done_all,
                "total": total_items_all,
                "overall_pct": round(100.0 * total_done_all / max(total_items_all, 1), 1),
            },
            "tracks": track_stats,
            "pipelines": pipelines,
            "review": review,
        }
    finally:
        conn.close()


# ------------------------------------------------------------------
# Pillar 2: Core Syllabus ("The Deep-Path")
# ------------------------------------------------------------------
@app.get("/api/syllabus")
def get_syllabus(daily_budget_min: int = 45):
    conn = get_conn()
    try:
        tracks = conn.execute("SELECT * FROM tracks ORDER BY sort_order").fetchall()
        out_tracks = []
        daily_candidates = []

        for tr in tracks:
            units = conn.execute(
                "SELECT * FROM units WHERE track_id = ? ORDER BY sort_order", (tr["id"],)
            ).fetchall()
            out_units = []
            for u in units:
                items = conn.execute(
                    """
                    SELECT i.id, i.kind, i.title, i.difficulty, i.xp, i.estimated_minutes, i.tags_json,
                           cp.status, cp.best_score, cp.attempts, cp.solved_via_placement,
                           fc.last_review_at, fc.stability
                    FROM items i
                    LEFT JOIN core_progress cp ON cp.item_id = i.id
                    LEFT JOIN fsrs_cards fc ON fc.item_id = i.id
                    WHERE i.unit_id = ?
                    ORDER BY i.sort_order
                    """,
                    (u["id"],),
                ).fetchall()
                vids = conn.execute("SELECT * FROM videos WHERE unit_id = ?", (u["id"],)).fetchall()

                item_list = []
                counts = {"puzzle": 0, "math": 0, "problem": 0, "debugging": 0, "lab": 0, "project": 0}
                done_count = 0
                for it in items:
                    counts[it["kind"]] = counts.get(it["kind"], 0) + 1
                    st = it["status"] or "unstarted"
                    if st == "completed":
                        done_count += 1
                    r = compute_retrievability(it["last_review_at"], it["stability"] or 4.0) if st == "completed" else 0.0
                    entry = {
                        "id": it["id"],
                        "kind": it["kind"],
                        "title": it["title"],
                        "difficulty": it["difficulty"],
                        "xp": it["xp"],
                        "estimated_minutes": it["estimated_minutes"],
                        "tags": load_json(it["tags_json"], []),
                        "status": st,
                        "best_score": it["best_score"] or 0.0,
                        "attempts": it["attempts"] or 0,
                        "solved_via_placement": bool(it["solved_via_placement"]),
                        "retrievability_pct": round(r * 100.0, 1),
                    }
                    item_list.append(entry)
                    if st != "completed":
                        daily_candidates.append({**entry, "unit_title": u["title"], "track_title": tr["title"]})

                out_units.append(
                    {
                        "id": u["id"],
                        "title": u["title"],
                        "prereq_ids": load_json(u["prereq_ids_json"], []),
                        "skills": load_json(u["skills_json"], []),
                        "estimated_minutes": u["estimated_minutes"],
                        "placement": load_json(u["placement_json"], {}),
                        "completed": done_count,
                        "total": len(item_list),
                        "counts": counts,
                        "items": item_list,
                        "videos": [
                            {
                                "id": v["id"],
                                "title": v["title"],
                                "creator": v["creator"],
                                "youtube_id": v["youtube_id"],
                                "duration_sec": v["duration_sec"],
                                "checkpoints": load_json(v["checkpoints_json"], []),
                            }
                            for v in vids
                        ],
                    }
                )
            out_tracks.append(
                {
                    "id": tr["id"],
                    "title": tr["title"],
                    "subtitle": tr["subtitle"],
                    "color": tr["color"],
                    "units": out_units,
                }
            )

        # Build Daily Time-Boxed Path fitting within daily_budget_min
        daily_plan = []
        used_min = 0
        for cand in daily_candidates:
            if used_min + cand["estimated_minutes"] <= daily_budget_min or not daily_plan:
                daily_plan.append(cand)
                used_min += cand["estimated_minutes"]
            if used_min >= daily_budget_min:
                break

        speed_run_ids = [
            "causal-multihead-attention",
            "flash-attention-online-softmax",
            "mlp-manual-backprop",
            "rope-positional-encoding",
            "paged-kv-cache-allocator",
            "causal-mask-sign-and-fp16-nan",
        ]
        research_practice_checklist = [
            {"id": "rp-1", "title": "Read a Paper Like a Referee", "prompt": "Separate empirical claims from unstated assumptions, compute budget, and cherry-picked baselines."},
            {"id": "rp-2", "title": "Reproduce One Mathematical Claim", "prompt": "Turn a single lemma or scaling equation from a paper into a 30-line falsifiable NumPy/PyTorch experiment."},
            {"id": "rp-3", "title": "Audit Training Data & Loss Contracts", "prompt": "Trace every tensor shape, mask sign, padding token exclusion, and gradient norm from dataloader to optimizer step."},
        ]

        return {
            "tracks": out_tracks,
            "daily_timebox": {
                "budget_minutes": daily_budget_min,
                "planned_minutes": used_min,
                "items": daily_plan,
            },
            "speed_run_ids": speed_run_ids,
            "research_practice": research_practice_checklist,
            "review": get_review_status(conn),
        }
    finally:
        conn.close()


@app.get("/api/items/{item_id}")
def get_item(item_id: str):
    conn = get_conn()
    try:
        it = conn.execute(
            """
            SELECT i.*, u.title AS unit_title, u.track_id, cp.status, cp.best_score, cp.attempts, cp.last_code
            FROM items i
            JOIN units u ON u.id = i.unit_id
            LEFT JOIN core_progress cp ON cp.item_id = i.id
            WHERE i.id = ?
            """,
            (item_id,),
        ).fetchone()
        if not it:
            raise HTTPException(status_code=404, detail=f"Item '{item_id}' not found")
        payload = load_json(it["payload_json"], {})
        vids = conn.execute("SELECT * FROM videos WHERE unit_id = ?", (it["unit_id"],)).fetchall()
        return {
            "id": it["id"],
            "kind": it["kind"],
            "unit_id": it["unit_id"],
            "unit_title": it["unit_title"],
            "track_id": it["track_id"],
            "title": it["title"],
            "difficulty": it["difficulty"],
            "xp": it["xp"],
            "estimated_minutes": it["estimated_minutes"],
            "tags": load_json(it["tags_json"], []),
            "status": it["status"] or "unstarted",
            "best_score": it["best_score"] or 0.0,
            "attempts": it["attempts"] or 0,
            "last_code": it["last_code"],
            "prompt_md": payload.get("prompt_md", ""),
            "theory_md": payload.get("theory_md", ""),
            "worked_example_md": payload.get("worked_example_md", ""),
            "drills": payload.get("drills", []),
            "milestones": payload.get("milestones", []),
            "metric_name": payload.get("metric_name"),
            "metric_goal": payload.get("metric_goal"),
            "starter_code": payload.get("starter_code", ""),
            "reference_code": payload.get("reference_code", ""),
            "videos": [
                {
                    "id": v["id"],
                    "title": v["title"],
                    "creator": v["creator"],
                    "youtube_id": v["youtube_id"],
                    "duration_sec": v["duration_sec"],
                    "checkpoints": load_json(v["checkpoints_json"], []),
                }
                for v in vids
            ],
        }
    finally:
        conn.close()


@app.post("/api/items/{item_id}/evaluate")
def evaluate_item(item_id: str, req: EvaluateItemRequest):
    conn = get_conn()
    try:
        it = conn.execute("SELECT * FROM items WHERE id = ?", (item_id,)).fetchone()
        if not it:
            raise HTTPException(status_code=404, detail=f"Item '{item_id}' not found")
        payload = load_json(it["payload_json"], {})
        kind = it["kind"]

        if kind == "math":
            res = evaluate_math_drills(payload.get("drills", []), req.math_answers or {})
        elif kind == "puzzle":
            res = evaluate_puzzle(req.code or "", payload.get("tests_code", ""))
        elif kind == "lab":
            res = evaluate_lab(req.code or "", payload.get("tests_code", ""))
        else:
            res = evaluate_code_problem(
                req.code or "",
                payload.get("tests_code", ""),
                banned_apis=payload.get("banned_apis", []),
                ban_matmul_op=bool(payload.get("ban_matmul_op", False)),
            )

        passed = bool(res.get("passed"))
        score = 100.0 if passed else float(res.get("score", 0.0))

        prev = conn.execute("SELECT * FROM core_progress WHERE item_id = ?", (item_id,)).fetchone()
        was_completed = bool(prev and prev["status"] == "completed")
        xp_awarded = int(it["xp"]) if (passed and not was_completed) else (15 if (passed and req.is_review) else 0)
        new_status = "completed" if (passed or was_completed) else "in_progress"
        best_score = max(score, float(prev["best_score"]) if prev else 0.0)
        attempts = (int(prev["attempts"]) if prev else 0) + 1
        total_item_xp = (int(prev["xp_earned"]) if prev else 0) + xp_awarded

        conn.execute(
            """
            INSERT INTO core_progress (item_id, status, best_score, attempts, xp_earned, solved_via_placement, last_code, last_practiced_at)
            VALUES (?, ?, ?, ?, ?, 0, ?, ?)
            ON CONFLICT(item_id) DO UPDATE SET
                status = excluded.status,
                best_score = excluded.best_score,
                attempts = excluded.attempts,
                xp_earned = excluded.xp_earned,
                last_code = COALESCE(excluded.last_code, core_progress.last_code),
                last_practiced_at = excluded.last_practiced_at
            """,
            (item_id, new_status, best_score, attempts, total_item_xp, req.code, utc_now()),
        )
        if xp_awarded > 0:
            conn.execute("UPDATE xp_state SET total_core_xp = total_core_xp + ? WHERE id = 1", (xp_awarded,))

        fsrs_info = update_fsrs_card(conn, item_id, it["unit_id"], passed=passed, studio_vulnerability=False)
        conn.commit()
        review_status = get_review_status(conn)

        return {
            "evaluation": res,
            "xp_awarded": xp_awarded,
            "fsrs": fsrs_info,
            "review": review_status,
        }
    finally:
        conn.close()


@app.post("/api/syllabus/placement/{unit_id}")
def submit_placement_quiz(unit_id: str, req: PlacementSubmitRequest):
    conn = get_conn()
    try:
        u = conn.execute("SELECT * FROM units WHERE id = ?", (unit_id,)).fetchone()
        if not u:
            raise HTTPException(status_code=404, detail=f"Unit '{unit_id}' not found")
        placement = load_json(u["placement_json"], {})
        keywords = placement.get("keywords", [])
        min_kw = int(placement.get("min_keywords", 2))
        low = (req.answer or "").lower()
        hits = [kw for kw in keywords if kw.lower() in low]
        passed = len(hits) >= min_kw and len(low.strip()) >= 30

        skipped_items = []
        if passed:
            items = conn.execute("SELECT id, xp FROM items WHERE unit_id = ?", (unit_id,)).fetchall()
            for it in items:
                conn.execute(
                    """
                    INSERT INTO core_progress (item_id, status, best_score, attempts, xp_earned, solved_via_placement, last_practiced_at)
                    VALUES (?, 'completed', 90.0, 1, 0, 1, ?)
                    ON CONFLICT(item_id) DO UPDATE SET status = 'completed', solved_via_placement = 1, last_practiced_at = excluded.last_practiced_at
                    """,
                    (it["id"], utc_now()),
                )
                update_fsrs_card(conn, it["id"], unit_id, passed=True, studio_vulnerability=False)
                skipped_items.append(it["id"])
            conn.commit()

        return {
            "unit_id": unit_id,
            "passed": passed,
            "matched_concepts": hits,
            "required_count": min_kw,
            "skipped_items": skipped_items,
            "feedback": (
                f"Placement verified ({len(hits)}/{min_kw} key concepts). Skipped {len(skipped_items)} items in '{u['title']}' and enrolled them in FSRS decay tracking."
                if passed
                else f"Need at least {min_kw} core mechanisms explained clearly (matched {len(hits)}: {hits}). Work through the unit first."
            ),
        }
    finally:
        conn.close()


@app.post("/api/syllabus/review/complete")
def complete_review_checkpoint():
    conn = get_conn()
    try:
        acknowledge_review_checkpoint(conn)
        return {"ok": True, "review": get_review_status(conn)}
    finally:
        conn.close()


# ------------------------------------------------------------------
# Private Profile (CV, STAR Stories, Project War-Room Dossiers) & Target JDs
# ------------------------------------------------------------------
@app.get("/api/profile")
def get_profile():
    conn = get_conn()
    try:
        row = conn.execute("SELECT * FROM user_profile WHERE id = 1").fetchone()
        return {
            "cv_markdown": row["cv_markdown"],
            "star_stories_markdown": row["star_stories_markdown"],
            "dossiers": load_json(row["dossiers_json"], {}),
            "updated_at": row["updated_at"],
        }
    finally:
        conn.close()


@app.put("/api/profile")
def update_profile(req: ProfileUpdateRequest):
    conn = get_conn()
    try:
        conn.execute(
            "UPDATE user_profile SET cv_markdown = ?, star_stories_markdown = ?, dossiers_json = ?, updated_at = ? WHERE id = 1",
            (req.cv_markdown, req.star_stories_markdown, json.dumps(req.dossiers), utc_now()),
        )
        # Re-map existing target roles against updated CV
        targets = conn.execute("SELECT id, jd_markdown FROM target_roles").fetchall()
        for t in targets:
            skills, ov, gap = map_jd_cv_to_items(conn, t["jd_markdown"], req.cv_markdown)
            conn.execute(
                "UPDATE target_roles SET parsed_skills_json = ?, cv_overlap_items_json = ?, jd_gap_items_json = ? WHERE id = ?",
                (json.dumps(skills), json.dumps(ov), json.dumps(gap), t["id"]),
            )
        conn.commit()
        return {"ok": True}
    finally:
        conn.close()


@app.get("/api/targets")
def list_targets():
    conn = get_conn()
    try:
        rows = conn.execute("SELECT * FROM target_roles ORDER BY created_at ASC").fetchall()
        out = []
        for r in rows:
            sessions = conn.execute(
                "SELECT id, current_stage, status, started_at, completed_at FROM studio_sessions WHERE target_id = ? ORDER BY started_at DESC",
                (r["id"],),
            ).fetchall()
            out.append(
                {
                    "id": r["id"],
                    "company": r["company"],
                    "role_title": r["role_title"],
                    "seniority": r["seniority"],
                    "target_date": r["target_date"],
                    "jd_markdown": r["jd_markdown"],
                    "parsed_skills": load_json(r["parsed_skills_json"], []),
                    "cv_overlap_items": load_json(r["cv_overlap_items_json"], []),
                    "jd_gap_items": load_json(r["jd_gap_items_json"], []),
                    "sessions": [dict(s) for s in sessions],
                }
            )
        return {"targets": out}
    finally:
        conn.close()


@app.post("/api/targets")
def create_target(req: CreateTargetRequest):
    conn = get_conn()
    try:
        slug = re.sub(r"[^a-z0-9]+", "-", f"{req.company}-{req.role_title}".lower()).strip("-")
        tid = f"{slug[:40]}-{uuid.uuid4().hex[:4]}"
        prof = conn.execute("SELECT cv_markdown FROM user_profile WHERE id = 1").fetchone()
        skills, ov, gap = map_jd_cv_to_items(conn, req.jd_markdown, prof["cv_markdown"] if prof else "")
        conn.execute(
            """
            INSERT INTO target_roles (id, company, role_title, seniority, target_date, jd_markdown, parsed_skills_json, cv_overlap_items_json, jd_gap_items_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                tid,
                req.company,
                req.role_title,
                req.seniority,
                req.target_date,
                req.jd_markdown,
                json.dumps(skills),
                json.dumps(ov),
                json.dumps(gap),
                utc_now(),
            ),
        )
        conn.commit()
        return {"id": tid, "parsed_skills": skills, "cv_overlap_items": ov, "jd_gap_items": gap}
    finally:
        conn.close()


@app.delete("/api/targets/{target_id}")
def delete_target(target_id: str):
    conn = get_conn()
    try:
        conn.execute("DELETE FROM target_roles WHERE id = ?", (target_id,))
        conn.commit()
        return {"ok": True}
    finally:
        conn.close()


# ------------------------------------------------------------------
# Pillar 3: Interview Studio (Gated 4-Stage Gauntlet)
# ------------------------------------------------------------------
@app.post("/api/studio/sessions")
def api_create_session(req: CreateSessionRequest):
    conn = get_conn()
    try:
        return create_studio_session(conn, req.target_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    finally:
        conn.close()


@app.get("/api/studio/sessions/{session_id}")
def api_get_session(session_id: str):
    conn = get_conn()
    try:
        return get_session_detail(conn, session_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    finally:
        conn.close()


@app.post("/api/studio/sessions/{session_id}/stage1/{item_id}")
def api_stage1(session_id: str, item_id: str, req: Stage1SubmitRequest):
    conn = get_conn()
    try:
        return submit_stage1_item(conn, session_id, item_id, code=req.code, math_answers=req.math_answers)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    finally:
        conn.close()


@app.post("/api/studio/sessions/{session_id}/stage2")
def api_stage2(session_id: str, req: Stage2SubmitRequest):
    conn = get_conn()
    try:
        return submit_stage2(
            conn,
            session_id,
            coding_code=req.coding_code,
            coding_duration_sec=req.coding_duration_sec,
            system_design_answer=req.system_design_answer,
            constraint_shift_answer=req.constraint_shift_answer,
            deep_knowledge_answer=req.deep_knowledge_answer,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    finally:
        conn.close()


@app.post("/api/studio/sessions/{session_id}/stage3")
def api_stage3(session_id: str, req: Stage3SubmitRequest):
    conn = get_conn()
    try:
        return submit_stage3(conn, session_id, answers=req.answers)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    finally:
        conn.close()


@app.post("/api/studio/sessions/{session_id}/stage4")
def api_stage4(session_id: str, req: Stage4SubmitRequest):
    conn = get_conn()
    try:
        return submit_stage4(conn, session_id, answers=req.answers, track_mode=req.track_mode)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    finally:
        conn.close()


# ------------------------------------------------------------------
# Phase 2: Predict-Before-Running Notes, 15-Min Stuck FSRS Flag, Flashcards & Application CRM
# ------------------------------------------------------------------
@app.get("/api/items/{item_id}/notes")
def get_item_notes(item_id: str):
    conn = get_conn()
    try:
        row = conn.execute("SELECT * FROM item_notes WHERE item_id = ?", (item_id,)).fetchone()
        if not row:
            return {"item_id": item_id, "expected_text": "", "observed_text": "", "why_text": "", "updated_at": None}
        return dict(row)
    finally:
        conn.close()


@app.put("/api/items/{item_id}/notes")
def save_item_notes(item_id: str, req: ItemNotesRequest):
    conn = get_conn()
    try:
        now = utc_now()
        conn.execute(
            """
            INSERT INTO item_notes (item_id, expected_text, observed_text, why_text, updated_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(item_id) DO UPDATE SET
                expected_text = excluded.expected_text,
                observed_text = excluded.observed_text,
                why_text = excluded.why_text,
                updated_at = excluded.updated_at
            """,
            (item_id, req.expected_text, req.observed_text, req.why_text, now),
        )
        conn.commit()
        return {"ok": True, "item_id": item_id, "updated_at": now}
    finally:
        conn.close()


@app.post("/api/syllabus/flag-stuck/{item_id}")
def flag_item_stuck(item_id: str):
    """Silvia Sapora 15-minute stuck rule: flag item for high-priority FSRS review and move on cleanly."""
    conn = get_conn()
    try:
        it = conn.execute("SELECT id, unit_id, title FROM items WHERE id = ?", (item_id,)).fetchone()
        if not it:
            raise HTTPException(status_code=404, detail=f"Item '{item_id}' not found")
        fsrs = update_fsrs_card(conn, it["id"], it["unit_id"], passed=False, studio_vulnerability=True)
        conn.commit()
        return {
            "ok": True,
            "item_id": item_id,
            "message": f"Flagged '{it['title']}' into FSRS review queue (3x urgency boost). Study the reference, log Expected/Observed/Why, and move on.",
            "fsrs": fsrs,
        }
    finally:
        conn.close()


@app.get("/api/flashcards")
def api_list_flashcards(category: str | None = None, only_authored: bool = False):
    conn = get_conn()
    try:
        return list_flashcards(conn, category=category, only_authored=only_authored)
    finally:
        conn.close()


@app.post("/api/flashcards")
def api_create_flashcard(req: CreateFlashcardRequest):
    conn = get_conn()
    try:
        cid = f"custom-{uuid.uuid4().hex[:8]}"
        authored = 1 if req.user_back_markdown.strip() else 0
        conn.execute(
            """
            INSERT INTO flashcards (id, category, topic, front_prompt, user_back_markdown, authored, due_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (cid, req.category, req.topic, req.front_prompt, req.user_back_markdown, authored, utc_now()),
        )
        conn.commit()
        return {"id": cid, "ok": True}
    finally:
        conn.close()


@app.put("/api/flashcards/{card_id}")
def api_update_flashcard(card_id: str, req: UpdateFlashcardRequest):
    conn = get_conn()
    try:
        row = conn.execute("SELECT * FROM flashcards WHERE id = ?", (card_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Flashcard not found")
        authored = 1 if req.user_back_markdown.strip() else 0
        front = req.front_prompt if req.front_prompt is not None else row["front_prompt"]
        due = row["due_at"] or utc_now()
        conn.execute(
            "UPDATE flashcards SET front_prompt = ?, user_back_markdown = ?, authored = ?, due_at = ? WHERE id = ?",
            (front, req.user_back_markdown, authored, due, card_id),
        )
        conn.commit()
        return {"ok": True, "id": card_id, "authored": bool(authored)}
    finally:
        conn.close()


@app.post("/api/flashcards/{card_id}/review")
def api_review_flashcard(card_id: str, req: ReviewFlashcardRequest):
    conn = get_conn()
    try:
        return review_flashcard(conn, card_id, req.rating)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    finally:
        conn.close()


@app.get("/api/crm")
def api_get_crm():
    conn = get_conn()
    try:
        targets = conn.execute("SELECT id, company, role_title, seniority, target_date FROM target_roles ORDER BY created_at").fetchall()
        records = []
        all_dates: list[tuple[str, str]] = []
        for t in targets:
            c = conn.execute("SELECT * FROM crm_pipelines WHERE target_id = ?", (t["id"],)).fetchone()
            dates = load_json(c["interview_dates_json"], []) if c else []
            offer = load_json(c["offer_json"], {}) if c else {}
            for d in dates:
                all_dates.append((d, f"{t['company']} ({t['role_title']})"))
            records.append(
                {
                    "target_id": t["id"],
                    "company": t["company"],
                    "role_title": t["role_title"],
                    "seniority": t["seniority"],
                    "target_date": t["target_date"],
                    "app_stage": c["app_stage"] if c else "Researching",
                    "referral_contact": c["referral_contact"] if c else "",
                    "cold_email_draft": c["cold_email_draft"] if c else "",
                    "interview_dates": dates,
                    "offer": offer,
                }
            )

        # Compute max 7-day rolling interview density (burnout spacing guardrail)
        parsed_dt = []
        for ds, label in all_dates:
            try:
                parsed_dt.append((datetime.fromisoformat(ds).date(), label))
            except Exception:
                pass
        parsed_dt.sort(key=lambda x: x[0])
        peak_7d = 0
        peak_window = None
        for i, (d0, _) in enumerate(parsed_dt):
            window = [item for item in parsed_dt[i:] if (item[0] - d0).days <= 6]
            if len(window) > peak_7d:
                peak_7d = len(window)
                peak_window = f"{d0.isoformat()} to {window[-1][0].isoformat()}"

        return {
            "records": records,
            "burnout_guardrail": {
                "peak_interviews_in_7_days": peak_7d,
                "peak_window": peak_window,
                "burnout_warning": peak_7d > 3,
                "advice": (
                    f"Burnout Warning: {peak_7d} interviews clustered in 7 days ({peak_window}). Space loops to <=3/week to protect sleep and peak recall."
                    if peak_7d > 3
                    else "Healthy interview spacing (<=3 loops per 7-day window)."
                ),
            },
        }
    finally:
        conn.close()


@app.put("/api/crm/{target_id}")
def api_update_crm(target_id: str, req: CrmUpdateRequest):
    conn = get_conn()
    try:
        conn.execute(
            """
            INSERT INTO crm_pipelines (target_id, app_stage, referral_contact, cold_email_draft, interview_dates_json, offer_json, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(target_id) DO UPDATE SET
                app_stage = excluded.app_stage,
                referral_contact = excluded.referral_contact,
                cold_email_draft = excluded.cold_email_draft,
                interview_dates_json = excluded.interview_dates_json,
                offer_json = excluded.offer_json,
                updated_at = excluded.updated_at
            """,
            (
                target_id,
                req.app_stage,
                req.referral_contact,
                req.cold_email_draft,
                json.dumps(req.interview_dates),
                json.dumps(req.offer),
                utc_now(),
            ),
        )
        conn.commit()
        return {"ok": True, "target_id": target_id}
    finally:
        conn.close()


@app.post("/api/studio/sessions/{session_id}/abort")
def api_abort_session(session_id: str):
    conn = get_conn()
    try:
        return abort_session(conn, session_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    finally:
        conn.close()


# ------------------------------------------------------------------
# Pillar 4: Prep Recap (Analytics & Diagnostics)
# ------------------------------------------------------------------
@app.get("/api/recap/{session_id}")
def api_get_recap(session_id: str):
    conn = get_conn()
    try:
        return build_recap(conn, session_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    finally:
        conn.close()


# ------------------------------------------------------------------
# Pillar 5: Readiness Score (JD vs. CV vs. Prep)
# ------------------------------------------------------------------
@app.get("/api/readiness/{target_id}")
def api_get_readiness(target_id: str):
    conn = get_conn()
    try:
        return compute_readiness_for_target(conn, target_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    finally:
        conn.close()
