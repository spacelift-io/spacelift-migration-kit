"""Batch CRUD operations."""

import sqlite3
from datetime import datetime, timezone
from typing import Any


def get_current_batch(db: sqlite3.Connection) -> dict[str, Any] | None:
    """Return the current draft batch, or None if no draft exists."""
    row = db.execute("SELECT * FROM batches WHERE status = 'draft' ORDER BY id DESC LIMIT 1").fetchone()
    if row is None:
        return None
    return dict(row)


def create_batch(db: sqlite3.Connection) -> dict[str, Any]:
    """Create a new draft batch. Raises ValueError if a draft already exists."""
    existing = get_current_batch(db)
    if existing is not None:
        raise ValueError(f"Draft batch #{existing['id']} already exists")
    created_at = datetime.now(timezone.utc).isoformat()
    cursor = db.execute(
        "INSERT INTO batches (created_at, status) VALUES (?, 'draft')",
        (created_at,),
    )
    db.commit()
    batch_id = cursor.lastrowid
    row = db.execute("SELECT * FROM batches WHERE id = ?", (batch_id,)).fetchone()
    return dict(row)


def confirm_batch(db: sqlite3.Connection, batch_id: int) -> dict[str, Any]:
    """Mark a batch as confirmed. Raises ValueError if not a draft."""
    row = db.execute("SELECT * FROM batches WHERE id = ?", (batch_id,)).fetchone()
    if row is None:
        raise ValueError(f"Batch #{batch_id} not found")
    if row["status"] != "draft":
        raise ValueError(f"Batch #{batch_id} is not a draft (status={row['status']})")
    db.execute("UPDATE batches SET status = 'confirmed' WHERE id = ?", (batch_id,))
    db.commit()
    row = db.execute("SELECT * FROM batches WHERE id = ?", (batch_id,)).fetchone()
    return dict(row)


def get_batch_stats(db: sqlite3.Connection, batch_id: int) -> dict[str, int]:
    """Return entity counts by status for a batch."""
    rows = db.execute(
        """
        SELECT status, COUNT(*) AS cnt
        FROM batch_entities
        WHERE batch_id = ?
        GROUP BY status
        """,
        (batch_id,),
    ).fetchall()
    stats: dict[str, int] = {}
    for row in rows:
        stats[row["status"]] = row["cnt"]
    stats["total"] = sum(stats.values())
    return stats
