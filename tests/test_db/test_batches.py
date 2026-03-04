"""Tests for batch CRUD operations."""

from pathlib import Path

import pytest

from smk.core.db.batches import confirm_batch, create_batch, get_batch_stats, get_current_batch
from smk.core.db.connection import get_db

_SQL_INSERT = "INSERT INTO batch_entities (batch_id, entity_type, entity_id, status) VALUES (?, 'workspaces', ?, ?)"


def _insert_entity(db, batch_id, entity_id, status):
    db.execute(_SQL_INSERT, (batch_id, entity_id, status))
    db.commit()


@pytest.fixture
def db(tmp_path: Path):
    conn = get_db(tmp_path)
    yield conn
    conn.close()


def test_get_current_batch_none_when_empty(db) -> None:
    """No current batch when DB is empty."""
    assert get_current_batch(db) is None


def test_create_batch_returns_dict(db) -> None:
    """create_batch returns a batch dict."""
    batch = create_batch(db)
    assert batch["id"] == 1
    assert batch["status"] == "draft"
    assert "created_at" in batch


def test_create_batch_conflict_raises(db) -> None:
    """create_batch raises ValueError if draft exists."""
    create_batch(db)
    with pytest.raises(ValueError, match="already exists"):
        create_batch(db)


def test_get_current_batch_returns_draft(db) -> None:
    """get_current_batch returns the draft."""
    create_batch(db)
    batch = get_current_batch(db)
    assert batch is not None
    assert batch["status"] == "draft"


def test_confirm_batch_changes_status(db) -> None:
    """confirm_batch changes status to confirmed."""
    batch = create_batch(db)
    confirmed = confirm_batch(db, batch["id"])
    assert confirmed["status"] == "confirmed"


def test_confirm_batch_not_found_raises(db) -> None:
    """confirm_batch raises ValueError for unknown id."""
    with pytest.raises(ValueError, match="not found"):
        confirm_batch(db, 999)


def test_confirm_batch_already_confirmed_raises(db) -> None:
    """confirm_batch raises ValueError if already confirmed."""
    batch = create_batch(db)
    confirm_batch(db, batch["id"])
    with pytest.raises(ValueError, match="not a draft"):
        confirm_batch(db, batch["id"])


def test_get_current_batch_none_after_confirm(db) -> None:
    """After confirming, no draft batch exists."""
    batch = create_batch(db)
    confirm_batch(db, batch["id"])
    assert get_current_batch(db) is None


def test_get_batch_stats_empty(db) -> None:
    """Stats for empty batch has total=0."""
    batch = create_batch(db)
    stats = get_batch_stats(db, batch["id"])
    assert stats["total"] == 0


def test_get_batch_stats_counts(db) -> None:
    """Stats aggregate entity statuses."""
    batch = create_batch(db)
    _insert_entity(db, batch["id"], "ws-1", "selected")
    _insert_entity(db, batch["id"], "ws-2", "ready")
    db.commit()
    stats = get_batch_stats(db, batch["id"])
    assert stats["selected"] == 1
    assert stats["ready"] == 1
    assert stats["total"] == 2
