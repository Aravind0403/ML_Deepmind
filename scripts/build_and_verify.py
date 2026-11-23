#!/usr/bin/env python3
"""Verify every content item deterministically and compile content/ + starter private/ into db/progress.sqlite."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from backend.db import get_conn, init_db, utc_now
from backend.engines.flashcards_engine import seed_frontier_flashcards
from backend.engines.studio_engine import map_jd_cv_to_items
from backend.evaluators.runners import (
    evaluate_code_problem,
    evaluate_lab,
    evaluate_math_drills,
    evaluate_puzzle,
)


def read_opt(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def parse_jd_header(jd_text: str, filename: str) -> dict[str, str | None]:
    meta: dict[str, str | None] = {
        "company": filename.split("_")[0].title(),
        "role_title": filename.replace("_", " ").title(),
        "seniority": "Staff",
        "target_date": None,
    }
    for line in jd_text.splitlines()[:10]:
        m = re.match(r"^(company|role_title|seniority|target_date)\s*:\s*(.+)$", line.strip(), re.I)
        if m:
            meta[m.group(1).lower()] = m.group(2).strip()
    return meta


def main() -> int:
    init_db()
    conn = get_conn()
    try:
        # 1. Load Unified 5-Track Taxonomy
        tax = yaml.safe_load((ROOT / "content" / "taxonomy.yaml").read_text(encoding="utf-8"))
        for tr in tax["tracks"]:
            conn.execute(
                """
                INSERT INTO tracks (id, title, subtitle, sort_order, color)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    title = excluded.title,
                    subtitle = excluded.subtitle,
                    sort_order = excluded.sort_order,
                    color = excluded.color
                """,
                (tr["id"], tr["title"], tr["subtitle"], int(tr["order"]), tr["color"]),
            )
            for idx, u in enumerate(tr["units"]):
                conn.execute(
                    """
                    INSERT INTO units (id, track_id, title, prereq_ids_json, skills_json, estimated_minutes, placement_json, sort_order)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        track_id = excluded.track_id,
                        title = excluded.title,
                        prereq_ids_json = excluded.prereq_ids_json,
                        skills_json = excluded.skills_json,
                        estimated_minutes = excluded.estimated_minutes,
                        placement_json = excluded.placement_json,
                        sort_order = excluded.sort_order
                    """,
                    (
                        u["id"],
                        tr["id"],
                        u["title"],
                        json.dumps(u.get("req", [])),
                        json.dumps(u.get("skills", [])),
                        int(u.get("estimated_minutes", 45)),
                        json.dumps(u.get("placement_question", {})),
                        idx + 1,
                    ),
                )

        # 2. Verify & Compile All Content Items
        item_dirs = sorted(p.parent for p in (ROOT / "content" / "items").rglob("meta.yaml"))
        print(f"Verifying {len(item_dirs)} content items through strict sandbox...")
        failures = 0

        for idir in item_dirs:
            meta = yaml.safe_load((idir / "meta.yaml").read_text(encoding="utf-8"))
            iid = meta["id"]
            kind = meta["kind"]

            payload = {
                "prompt_md": read_opt(idir / "prompt.md"),
                "theory_md": read_opt(idir / "theory.md"),
                "worked_example_md": read_opt(idir / "worked_example.md"),
                "starter_code": read_opt(idir / "starter.py"),
                "reference_code": read_opt(idir / "reference.py"),
                "tests_code": read_opt(idir / "tests.py"),
                "banned_apis": meta.get("banned_apis", []),
                "ban_matmul_op": bool(meta.get("ban_matmul_op", False)),
                "milestones": meta.get("milestones", []),
                "metric_name": meta.get("metric_name"),
                "metric_goal": meta.get("metric_goal"),
            }

            if kind == "math":
                drills_doc = yaml.safe_load((idir / "drills.yaml").read_text(encoding="utf-8"))
                payload["drills"] = drills_doc["drills"]
                good_ans = {d["id"]: str(d["expected"]) for d in payload["drills"]}
                bad_ans = {d["id"]: "999999" for d in payload["drills"]}
                res_ok = evaluate_math_drills(payload["drills"], good_ans)
                res_bad = evaluate_math_drills(payload["drills"], bad_ans)
            elif kind == "puzzle":
                res_ok = evaluate_puzzle(payload["reference_code"], payload["tests_code"])
                res_bad = evaluate_puzzle(payload["starter_code"], payload["tests_code"])
            elif kind == "lab":
                res_ok = evaluate_lab(payload["reference_code"], payload["tests_code"])
                res_bad = evaluate_lab(payload["starter_code"], payload["tests_code"])
            else:
                res_ok = evaluate_code_problem(
                    payload["reference_code"],
                    payload["tests_code"],
                    banned_apis=payload["banned_apis"],
                    ban_matmul_op=payload["ban_matmul_op"],
                )
                res_bad = evaluate_code_problem(
                    payload["starter_code"],
                    payload["tests_code"],
                    banned_apis=payload["banned_apis"],
                    ban_matmul_op=payload["ban_matmul_op"],
                )

            if not res_ok.get("passed"):
                print(f"  [FAIL] {iid} ({kind}): reference solution FAILED -> {res_ok}")
                failures += 1
                continue
            if res_bad.get("passed"):
                print(f"  [FAIL] {iid} ({kind}): starter code unexpectedly PASSED!")
                failures += 1
                continue

            print(f"  [PASS] {iid:36s} ({kind:7s}) ref=PASS starter=FAIL ({res_ok.get('elapsed_ms', 0)} ms)")
            conn.execute(
                """
                INSERT INTO items (id, kind, unit_id, title, difficulty, xp, estimated_minutes, tags_json, payload_json, sort_order)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    kind = excluded.kind,
                    unit_id = excluded.unit_id,
                    title = excluded.title,
                    difficulty = excluded.difficulty,
                    xp = excluded.xp,
                    estimated_minutes = excluded.estimated_minutes,
                    tags_json = excluded.tags_json,
                    payload_json = excluded.payload_json,
                    sort_order = excluded.sort_order
                """,
                (
                    iid,
                    kind,
                    meta["unit_id"],
                    meta["title"],
                    meta.get("difficulty", "medium"),
                    int(meta.get("xp", 35)),
                    int(meta.get("estimated_minutes", 15)),
                    json.dumps(meta.get("tags", [])),
                    json.dumps(payload),
                    int(meta.get("order", 1)),
                ),
            )

        if failures > 0:
            print(f"\nAborting: {failures} item(s) failed deterministic self-verification.")
            return 1

        # 3. Load Embedded YouTube Checkpoint Lectures
        vids_file = ROOT / "content" / "videos" / "lectures.yaml"
        if vids_file.exists():
            vids = yaml.safe_load(vids_file.read_text(encoding="utf-8")) or []
            for v in vids:
                conn.execute(
                    """
                    INSERT INTO videos (id, unit_id, title, creator, youtube_id, duration_sec, checkpoints_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        unit_id = excluded.unit_id,
                        title = excluded.title,
                        creator = excluded.creator,
                        youtube_id = excluded.youtube_id,
                        duration_sec = excluded.duration_sec,
                        checkpoints_json = excluded.checkpoints_json
                    """,
                    (
                        v["id"],
                        v["unit_id"],
                        v["title"],
                        v["creator"],
                        v["youtube_id"],
                        int(v["duration_sec"]),
                        json.dumps(v.get("checkpoints", [])),
                    ),
                )
            print(f"Loaded {len(vids)} YouTube checkpoint lecture configs.")

        # 4. Seed Private CV, STAR Stories, War-Room Dossiers & Starter Target JDs (only if empty)
        priv_dir = ROOT / "private"
        prof = conn.execute("SELECT cv_markdown FROM user_profile WHERE id = 1").fetchone()
        cv_text = prof["cv_markdown"] if prof else ""
        if not cv_text.strip() and (priv_dir / "cv.md").exists():
            cv_text = read_opt(priv_dir / "cv.md")
            star_text = read_opt(priv_dir / "star_stories.md")
            dossiers = {}
            if (priv_dir / "dossiers").exists():
                for dp in sorted((priv_dir / "dossiers").glob("*.md")):
                    dossiers[dp.stem] = dp.read_text(encoding="utf-8")
            conn.execute(
                "UPDATE user_profile SET cv_markdown = ?, star_stories_markdown = ?, dossiers_json = ?, updated_at = ? WHERE id = 1",
                (cv_text, star_text, json.dumps(dossiers), utc_now()),
            )
            print("Loaded private CV, STAR story bank, and Project War-Room Dossiers into local SQLite.")

        existing_targets = conn.execute("SELECT COUNT(*) AS c FROM target_roles").fetchone()["c"]
        if existing_targets == 0 and (priv_dir / "jds").exists():
            for jdp in sorted((priv_dir / "jds").glob("*.md")):
                jd_md = jdp.read_text(encoding="utf-8")
                hdr = parse_jd_header(jd_md, jdp.stem)
                skills, ov, gap = map_jd_cv_to_items(conn, jd_md, cv_text)
                conn.execute(
                    """
                    INSERT INTO target_roles (id, company, role_title, seniority, target_date, jd_markdown, parsed_skills_json, cv_overlap_items_json, jd_gap_items_json, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        jdp.stem,
                        hdr["company"],
                        hdr["role_title"],
                        hdr["seniority"],
                        hdr["target_date"],
                        jd_md,
                        json.dumps(skills),
                        json.dumps(ov),
                        json.dumps(gap),
                        utc_now(),
                    ),
                )
            print("Seeded 3 starter Target Company Pipelines from private/jds/.")

        # 5. Seed Silvia Sapora 115+ Author-Your-Own Frontier Flashcard Index
        fc_new = seed_frontier_flashcards(conn)
        fc_total = conn.execute("SELECT COUNT(*) AS c FROM flashcards").fetchone()["c"]
        print(f"Frontier Flashcards indexed: {fc_total} total ({fc_new} newly added).")

        conn.commit()
        print("\nSUCCESS: All items verified and compiled into db/progress.sqlite.")
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
