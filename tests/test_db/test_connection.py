"""Tests for DB connection and schema initialization."""

import sqlite3
from pathlib import Path

from smk.core.db.connection import get_db, init_db


def test_get_db_creates_file(tmp_path: Path) -> None:
    """get_db creates db file in config dir."""
    conn = get_db(tmp_path)
    assert (tmp_path / "smk.db").exists()
    conn.close()


def test_get_db_returns_connection(tmp_path: Path) -> None:
    """get_db returns a sqlite3.Connection."""
    conn = get_db(tmp_path)
    assert isinstance(conn, sqlite3.Connection)
    conn.close()


def test_get_db_schema_idempotent(tmp_path: Path) -> None:
    """Calling get_db twice does not raise (schema is idempotent)."""
    conn1 = get_db(tmp_path)
    conn1.close()
    conn2 = get_db(tmp_path)
    conn2.close()


def test_get_db_creates_batches_table(tmp_path: Path) -> None:
    """batches table is created."""
    conn = get_db(tmp_path)
    tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
    assert "batches" in tables
    conn.close()


def test_get_db_creates_batch_entities_table(tmp_path: Path) -> None:
    """batch_entities table is created."""
    conn = get_db(tmp_path)
    tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
    assert "batch_entities" in tables
    conn.close()


def test_get_db_row_factory_set(tmp_path: Path) -> None:
    """row_factory is sqlite3.Row."""
    conn = get_db(tmp_path)
    assert conn.row_factory is sqlite3.Row
    conn.close()


def test_init_db_creates_file(tmp_path: Path) -> None:
    """init_db creates db file."""
    init_db(tmp_path)
    assert (tmp_path / "smk.db").exists()


def test_init_db_is_idempotent(tmp_path: Path) -> None:
    """init_db can be called multiple times without error."""
    init_db(tmp_path)
    init_db(tmp_path)


def test_get_db_default_uses_smk_config() -> None:
    """get_db with no args uses default config dir."""
    from smk.core.config.paths import get_db_path

    default_path = get_db_path()
    assert default_path.name == "smk.db"
