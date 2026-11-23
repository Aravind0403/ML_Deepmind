"""SQLite persistence layer for the private ML Command Center."""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parent.parent
DB_PATH = ROOT_DIR / "db" / "progress.sqlite"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA synchronous = NORMAL;")
    return conn


def init_db() -> None:
    conn = get_conn()
    try:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS tracks (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                subtitle TEXT NOT NULL,
                sort_order INTEGER NOT NULL,
                color TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS units (
                id TEXT PRIMARY KEY,
                track_id TEXT NOT NULL REFERENCES tracks(id) ON DELETE CASCADE,
                title TEXT NOT NULL,
                prereq_ids_json TEXT NOT NULL DEFAULT '[]',
                skills_json TEXT NOT NULL DEFAULT '[]',
                estimated_minutes INTEGER NOT NULL DEFAULT 45,
                placement_json TEXT NOT NULL DEFAULT '{}',
                sort_order INTEGER NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS items (
                id TEXT PRIMARY KEY,
                kind TEXT NOT NULL, -- puzzle | math | problem | lab | project
                unit_id TEXT NOT NULL REFERENCES units(id) ON DELETE CASCADE,
                title TEXT NOT NULL,
                difficulty TEXT NOT NULL,
                xp INTEGER NOT NULL DEFAULT 30,
                estimated_minutes INTEGER NOT NULL DEFAULT 15,
                tags_json TEXT NOT NULL DEFAULT '[]',
                payload_json TEXT NOT NULL DEFAULT '{}',
                sort_order INTEGER NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS videos (
                id TEXT PRIMARY KEY,
                unit_id TEXT NOT NULL REFERENCES units(id) ON DELETE CASCADE,
                title TEXT NOT NULL,
                creator TEXT NOT NULL,
                youtube_id TEXT NOT NULL,
                duration_sec INTEGER NOT NULL,
                checkpoints_json TEXT NOT NULL DEFAULT '[]'
            );

            CREATE TABLE IF NOT EXISTS core_progress (
                item_id TEXT PRIMARY KEY REFERENCES items(id) ON DELETE CASCADE,
                status TEXT NOT NULL DEFAULT 'unstarted', -- unstarted | in_progress | completed
                best_score REAL NOT NULL DEFAULT 0.0,
                attempts INTEGER NOT NULL DEFAULT 0,
                xp_earned INTEGER NOT NULL DEFAULT 0,
                solved_via_placement INTEGER NOT NULL DEFAULT 0,
                last_code TEXT DEFAULT NULL,
                last_practiced_at TEXT DEFAULT NULL
            );

            CREATE TABLE IF NOT EXISTS fsrs_cards (
                item_id TEXT PRIMARY KEY REFERENCES items(id) ON DELETE CASCADE,
                unit_id TEXT NOT NULL,
                stability REAL NOT NULL DEFAULT 3.0, -- days
                difficulty REAL NOT NULL DEFAULT 5.0, -- 1..10
                reps INTEGER NOT NULL DEFAULT 0,
                lapses INTEGER NOT NULL DEFAULT 0,
                studio_boost REAL NOT NULL DEFAULT 1.0,
                last_review_at TEXT DEFAULT NULL,
                due_at TEXT DEFAULT NULL
            );

            CREATE TABLE IF NOT EXISTS xp_state (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                total_core_xp INTEGER NOT NULL DEFAULT 0,
                last_review_xp_checkpoint INTEGER NOT NULL DEFAULT 0,
                review_threshold INTEGER NOT NULL DEFAULT 150
            );

            CREATE TABLE IF NOT EXISTS user_profile (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                cv_markdown TEXT NOT NULL DEFAULT '',
                star_stories_markdown TEXT NOT NULL DEFAULT '',
                dossiers_json TEXT NOT NULL DEFAULT '{}',
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS target_roles (
                id TEXT PRIMARY KEY,
                company TEXT NOT NULL,
                role_title TEXT NOT NULL,
                seniority TEXT NOT NULL DEFAULT 'Staff',
                target_date TEXT DEFAULT NULL,
                jd_markdown TEXT NOT NULL,
                parsed_skills_json TEXT NOT NULL DEFAULT '[]',
                cv_overlap_items_json TEXT NOT NULL DEFAULT '[]',
                jd_gap_items_json TEXT NOT NULL DEFAULT '[]',
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS studio_sessions (
                id TEXT PRIMARY KEY,
                target_id TEXT NOT NULL REFERENCES target_roles(id) ON DELETE CASCADE,
                current_stage INTEGER NOT NULL DEFAULT 1,
                status TEXT NOT NULL DEFAULT 'active', -- active | completed | aborted
                plan_json TEXT NOT NULL DEFAULT '{}',
                stage_results_json TEXT NOT NULL DEFAULT '{}',
                started_at TEXT NOT NULL,
                completed_at TEXT DEFAULT NULL
            );

            CREATE TABLE IF NOT EXISTS readiness_snapshots (
                id TEXT PRIMARY KEY,
                target_id TEXT NOT NULL REFERENCES target_roles(id) ON DELETE CASCADE,
                session_id TEXT NOT NULL REFERENCES studio_sessions(id) ON DELETE CASCADE,
                composite_score REAL NOT NULL,
                effective_score REAL NOT NULL,
                cv_fit REAL NOT NULL,
                jd_coverage REAL NOT NULL,
                execution_score REAL NOT NULL,
                delta_to_bar REAL NOT NULL,
                veto_blocked_by TEXT DEFAULT NULL,
                confidence_margin REAL NOT NULL,
                go_no_go TEXT NOT NULL,
                hc_memo_markdown TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS item_notes (
                item_id TEXT PRIMARY KEY REFERENCES items(id) ON DELETE CASCADE,
                expected_text TEXT NOT NULL DEFAULT '',
                observed_text TEXT NOT NULL DEFAULT '',
                why_text TEXT NOT NULL DEFAULT '',
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS flashcards (
                id TEXT PRIMARY KEY,
                category TEXT NOT NULL,
                topic TEXT NOT NULL,
                front_prompt TEXT NOT NULL,
                user_back_markdown TEXT NOT NULL DEFAULT '',
                authored INTEGER NOT NULL DEFAULT 0,
                stability REAL NOT NULL DEFAULT 2.0,
                difficulty REAL NOT NULL DEFAULT 5.0,
                reps INTEGER NOT NULL DEFAULT 0,
                lapses INTEGER NOT NULL DEFAULT 0,
                last_review_at TEXT DEFAULT NULL,
                due_at TEXT DEFAULT NULL
            );

            CREATE TABLE IF NOT EXISTS crm_pipelines (
                target_id TEXT PRIMARY KEY REFERENCES target_roles(id) ON DELETE CASCADE,
                app_stage TEXT NOT NULL DEFAULT 'Researching',
                referral_contact TEXT NOT NULL DEFAULT '',
                cold_email_draft TEXT NOT NULL DEFAULT '',
                interview_dates_json TEXT NOT NULL DEFAULT '[]',
                offer_json TEXT NOT NULL DEFAULT '{}',
                updated_at TEXT NOT NULL
            );
            """
        )
        conn.execute(
            "INSERT OR IGNORE INTO xp_state (id, total_core_xp, last_review_xp_checkpoint, review_threshold) VALUES (1, 0, 0, 150)"
        )
        conn.execute(
            "INSERT OR IGNORE INTO user_profile (id, cv_markdown, star_stories_markdown, dossiers_json, updated_at) VALUES (1, '', '', '{}', ?)",
            (utc_now(),),
        )
        conn.commit()
    finally:
        conn.close()


def row_to_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    if row is None:
        return None
    return {k: row[k] for k in row.keys()}


def load_json(text: str | None, default: Any) -> Any:
    if not text:
        return default
    try:
        return json.loads(text)
    except Exception:
        return default
