"""SQLite connection factory and schema initialization."""

import sqlite3
from pathlib import Path

from smk.core.config.paths import get_db_path

_SCHEMA = """
CREATE TABLE IF NOT EXISTS batches (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    status     TEXT NOT NULL DEFAULT 'draft'
);

CREATE TABLE IF NOT EXISTS batch_entities (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    batch_id          INTEGER NOT NULL REFERENCES batches(id) ON DELETE CASCADE,
    entity_type       TEXT NOT NULL,
    entity_id         TEXT NOT NULL,
    entity_name       TEXT NOT NULL DEFAULT '',
    parent_type       TEXT,
    parent_id         TEXT,
    auto_included     INTEGER NOT NULL DEFAULT 0,
    status            TEXT NOT NULL DEFAULT 'selected',
    source_entity     TEXT NOT NULL DEFAULT '{}',
    spacelift_entity  TEXT,
    hcl_resource_name TEXT,
    error_message     TEXT,
    transformed_at    TEXT,
    UNIQUE(entity_type, entity_id)
);

CREATE INDEX IF NOT EXISTS idx_be_batch ON batch_entities(batch_id);
CREATE INDEX IF NOT EXISTS idx_be_type  ON batch_entities(entity_type);
"""


def get_db(config_dir: Path | None = None) -> sqlite3.Connection:
    """Get a SQLite connection, initializing the schema if needed.

    Args:
        config_dir: Optional custom config directory. Uses default if None.

    Returns:
        Configured SQLite connection with row_factory set.
    """
    db_path = get_db_path(config_dir)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(_SCHEMA)
    return conn


def init_db(config_dir: Path | None = None) -> None:
    """Initialize the database schema idempotently.

    Args:
        config_dir: Optional custom config directory. Uses default if None.
    """
    conn = get_db(config_dir)
    conn.close()
