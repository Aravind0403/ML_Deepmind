"""FSRS memory decay & 150-XP Spaced Repetition Scheduler."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import sqlite3
from typing import Any

from backend.db import utc_now


def parse_iso(ts: str | None) -> datetime | None:
    if not ts:
        return None
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except Exception:
        return None


def compute_retrievability(last_review_at: str | None, stability_days: float) -> float:
    """FSRS power-law forgetting curve: R(t, S) = (1 + t / (9 * S))^-1."""
    dt = parse_iso(last_review_at)
    if dt is None:
        return 0.0
    elapsed_days = max(0.0, (datetime.now(timezone.utc) - dt).total_seconds() / 86400.0)
    s = max(0.5, float(stability_days))
    return float((1.0 + elapsed_days / (9.0 * s)) ** -1.0)


def update_fsrs_card(
    conn: sqlite3.Connection,
    item_id: str,
    unit_id: str,
    passed: bool,
    studio_vulnerability: bool = False,
) -> dict[str, Any]:
    """Update FSRS stability/difficulty after a practice attempt or Studio failure."""
    now = datetime.now(timezone.utc)
    now_iso = now.isoformat()
    row = conn.execute("SELECT * FROM fsrs_cards WHERE item_id = ?", (item_id,)).fetchone()

    if row is None:
        stability = 4.0 if passed else 1.0
        difficulty = 4.5 if passed else 7.0
        reps = 1 if passed else 0
        lapses = 0 if passed else 1
        boost = 3.0 if studio_vulnerability else 1.0
    else:
        stability = float(row["stability"])
        difficulty = float(row["difficulty"])
        reps = int(row["reps"])
        lapses = int(row["lapses"])
        boost = float(row["studio_boost"])
        if passed:
            reps += 1
            r = compute_retrievability(row["last_review_at"], stability)
            # FSRS-inspired stability growth
            stability = min(180.0, stability * (1.0 + 0.8 * (11.0 - difficulty) * (1.2 - r)))
            difficulty = max(1.0, difficulty - 0.3)
            boost = max(1.0, boost * 0.6)
        else:
            lapses += 1
            stability = max(0.75, stability * 0.45)
            difficulty = min(10.0, difficulty + 0.8)
            if studio_vulnerability:
                boost = 3.0

    due_days = max(0.25, stability / boost)
    due_at = (now + timedelta(days=due_days)).isoformat()

    conn.execute(
        """
        INSERT INTO fsrs_cards (item_id, unit_id, stability, difficulty, reps, lapses, studio_boost, last_review_at, due_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(item_id) DO UPDATE SET
            stability = excluded.stability,
            difficulty = excluded.difficulty,
            reps = excluded.reps,
            lapses = excluded.lapses,
            studio_boost = excluded.studio_boost,
            last_review_at = excluded.last_review_at,
            due_at = excluded.due_at
        """,
        (item_id, unit_id, round(stability, 2), round(difficulty, 2), reps, lapses, round(boost, 2), now_iso, due_at),
    )
    return {
        "item_id": item_id,
        "stability_days": round(stability, 2),
        "difficulty": round(difficulty, 2),
        "studio_boost": round(boost, 2),
        "due_at": due_at,
    }


def get_review_status(conn: sqlite3.Connection) -> dict[str, Any]:
    """Check 150-XP review trigger and return FSRS-prioritized review queue."""
    xp_row = conn.execute("SELECT * FROM xp_state WHERE id = 1").fetchone()
    total_xp = int(xp_row["total_core_xp"]) if xp_row else 0
    last_cp = int(xp_row["last_review_xp_checkpoint"]) if xp_row else 0
    threshold = int(xp_row["review_threshold"]) if xp_row else 150
    xp_since = total_xp - last_cp
    review_due_by_xp = xp_since >= threshold

    cards = conn.execute(
        """
        SELECT f.*, i.title, i.kind, i.difficulty AS item_difficulty, i.xp
        FROM fsrs_cards f
        JOIN items i ON i.id = f.item_id
        """
    ).fetchall()

    queue = []
    for c in cards:
        r = compute_retrievability(c["last_review_at"], c["stability"])
        # Priority combines forgetting urgency (1 - R) and 3x Studio vulnerability boost
        urgency = (1.0 - r + 0.15) * float(c["studio_boost"])
        queue.append(
            {
                "item_id": c["item_id"],
                "unit_id": c["unit_id"],
                "title": c["title"],
                "kind": c["kind"],
                "difficulty": c["item_difficulty"],
                "retrievability_pct": round(r * 100.0, 1),
                "stability_days": c["stability"],
                "studio_boost": c["studio_boost"],
                "urgency": round(urgency, 3),
                "due_at": c["due_at"],
            }
        )
    queue.sort(key=lambda x: -x["urgency"])

    return {
        "total_core_xp": total_xp,
        "xp_since_last_review": xp_since,
        "review_threshold": threshold,
        "review_triggered": review_due_by_xp,
        "xp_to_next_review": max(0, threshold - xp_since),
        "queue": queue[:6],
    }


def acknowledge_review_checkpoint(conn: sqlite3.Connection) -> None:
    """Reset the 150-XP trigger checkpoint once the user completes a review pass."""
    xp_row = conn.execute("SELECT total_core_xp FROM xp_state WHERE id = 1").fetchone()
    total_xp = int(xp_row["total_core_xp"]) if xp_row else 0
    conn.execute("UPDATE xp_state SET last_review_xp_checkpoint = ? WHERE id = 1", (total_xp,))
    conn.commit()
