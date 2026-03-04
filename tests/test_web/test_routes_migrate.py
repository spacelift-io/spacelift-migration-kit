"""Tests for /api/migrate/* endpoints."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

_SQL_ORG_READY = (
    "INSERT INTO batch_entities"
    " (batch_id, entity_type, entity_id, entity_name, status)"
    " VALUES (?, 'organizations', 'o-1', 'x', 'ready')"
)
_SQL_WS_SEL = (
    "INSERT INTO batch_entities"
    " (batch_id, entity_type, entity_id, entity_name, status)"
    " VALUES (?, 'workspaces', 'ws-1', 'x', 'selected')"
)


@pytest.fixture
def db_client(tmp_path: Path, client: TestClient):
    """Patch _get_db to use a temp DB."""
    from smk.core.db import get_db

    def _make_db(_request=None):
        return get_db(tmp_path)

    with patch("smk.core.web.routes.migrate._get_db", side_effect=_make_db):
        yield client, tmp_path


def test_get_current_batch_empty(db_client) -> None:
    """GET /api/migrate/batch/current returns {} when no batch."""
    client, _ = db_client
    response = client.get("/api/migrate/batch/current")
    assert response.status_code == 200
    assert response.json() == {}


def test_create_batch(db_client) -> None:
    """POST /api/migrate/batch creates a draft batch."""
    client, _ = db_client
    response = client.post("/api/migrate/batch")
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "draft"
    assert data["id"] == 1


def test_create_batch_conflict(db_client) -> None:
    """POST /api/migrate/batch returns 409 if draft exists."""
    client, _ = db_client
    client.post("/api/migrate/batch")
    response = client.post("/api/migrate/batch")
    assert response.status_code == 409


def test_get_current_batch_after_create(db_client) -> None:
    """GET /api/migrate/batch/current returns batch after creation."""
    client, _ = db_client
    client.post("/api/migrate/batch")
    response = client.get("/api/migrate/batch/current")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert "stats" in data


def test_discard_batch(db_client) -> None:
    """DELETE /api/migrate/batch/{id} discards draft."""
    client, _ = db_client
    client.post("/api/migrate/batch")
    response = client.delete("/api/migrate/batch/1")
    assert response.status_code == 200
    assert response.json()["deleted"] is True


def test_discard_batch_not_found(db_client) -> None:
    """DELETE /api/migrate/batch/999 returns 404."""
    client, _ = db_client
    response = client.delete("/api/migrate/batch/999")
    assert response.status_code == 404


def test_discard_confirmed_batch_returns_400(db_client, tmp_path: Path) -> None:
    """DELETE /api/migrate/batch/{id} returns 400 for confirmed batch."""
    client, tmp_path = db_client
    from smk.core.db import get_db
    from smk.core.db.batches import confirm_batch, create_batch

    db = get_db(tmp_path)
    batch = create_batch(db)
    db.execute(
        _SQL_ORG_READY,
        (batch["id"],),
    )
    db.commit()
    confirm_batch(db, batch["id"])
    db.close()

    response = client.delete(f"/api/migrate/batch/{batch['id']}")
    assert response.status_code == 400


def test_list_entities_no_source(db_client, tmp_path: Path) -> None:
    """GET /api/migrate/entities returns empty when no source files."""
    client, tmp_path = db_client
    empty_src = tmp_path / "empty_src"
    empty_src.mkdir()
    with patch("smk.core.db.entities._get_source_dir", return_value=empty_src):
        response = client.get("/api/migrate/entities?type=workspaces")
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0


def test_list_entities_with_source(db_client, tmp_path: Path) -> None:
    """GET /api/migrate/entities returns entities from source files."""
    client, tmp_path = db_client
    workspaces = [{"id": "ws-1", "name": "prod"}]
    actual_src = tmp_path / "src"
    actual_src.mkdir()
    (actual_src / "workspaces.json").write_text(json.dumps(workspaces))
    with patch("smk.core.db.entities._get_source_dir", return_value=actual_src):
        response = client.get("/api/migrate/entities?type=workspaces")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["entity_id"] == "ws-1"


def test_select_entities_creates_batch_if_none(db_client) -> None:
    """POST /api/migrate/entities/select auto-creates batch if none exists."""
    client, _ = db_client
    with patch("smk.core.web.routes.migrate._load_source_entities", return_value=[]):
        response = client.post(
            "/api/migrate/entities/select",
            json={"entity_type": "workspaces", "entity_ids": [], "selected": True},
        )
    assert response.status_code == 200


def test_select_entities_deselect(db_client, tmp_path: Path) -> None:
    """POST /api/migrate/entities/select with selected=False removes entities."""
    client, tmp_path = db_client
    from smk.core.db import get_db
    from smk.core.db.batches import create_batch

    db = get_db(tmp_path)
    batch = create_batch(db)
    db.execute(
        _SQL_WS_SEL,
        (batch["id"],),
    )
    db.commit()
    db.close()

    response = client.post(
        "/api/migrate/entities/select",
        json={"entity_type": "workspaces", "entity_ids": ["ws-1"], "selected": False},
    )
    assert response.status_code == 200
    assert response.json()["removed"] == 1


def test_get_batch_entities_endpoint(db_client, tmp_path: Path) -> None:
    """GET /api/migrate/batch/{id}/entities returns full entity data."""
    client, tmp_path = db_client
    from smk.core.db import get_db
    from smk.core.db.batches import create_batch

    db = get_db(tmp_path)
    batch = create_batch(db)
    db.execute(
        _SQL_WS_SEL,
        (batch["id"],),
    )
    db.commit()
    db.close()

    response = client.get(f"/api/migrate/batch/{batch['id']}/entities")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["entity_id"] == "ws-1"
    assert "source_entity" in data[0]


def test_transform_status_returns_stats(db_client, tmp_path: Path) -> None:
    """GET /api/migrate/batch/{id}/transform/status returns stats dict."""
    client, tmp_path = db_client
    from smk.core.db import get_db
    from smk.core.db.batches import create_batch

    db = get_db(tmp_path)
    batch = create_batch(db)
    db.close()

    response = client.get(f"/api/migrate/batch/{batch['id']}/transform/status")
    assert response.status_code == 200
    data = response.json()
    assert "total" in data


def test_start_transform_not_found(db_client) -> None:
    """POST /api/migrate/batch/999/transform returns 404."""
    client, _ = db_client
    response = client.post("/api/migrate/batch/999/transform")
    assert response.status_code == 404


def test_start_transform_not_draft(db_client, tmp_path: Path) -> None:
    """POST /api/migrate/batch/{id}/transform returns 400 for confirmed batch."""
    client, tmp_path = db_client
    from smk.core.db import get_db
    from smk.core.db.batches import confirm_batch, create_batch

    db = get_db(tmp_path)
    batch = create_batch(db)
    db.execute(
        _SQL_ORG_READY,
        (batch["id"],),
    )
    db.commit()
    confirm_batch(db, batch["id"])
    db.close()

    response = client.post(f"/api/migrate/batch/{batch['id']}/transform")
    assert response.status_code == 400


def test_get_source_plugin_returns_empty_when_not_configured() -> None:
    """_get_source_plugin returns '' when config not initialized."""
    from smk.core.exceptions import ConfigNotInitializedError
    from smk.core.web.routes.migrate import _get_source_plugin

    with patch("smk.core.web.routes.migrate.ConfigManager") as mock_cm:
        mock_cm.return_value.load.side_effect = ConfigNotInitializedError
        result = _get_source_plugin()
    assert result == ""


def test_get_source_plugin_returns_plugin_name() -> None:
    """_get_source_plugin returns source plugin name."""
    from unittest.mock import MagicMock

    from smk.core.web.routes.migrate import _get_source_plugin

    mock_cfg = MagicMock()
    mock_cfg.source.plugin = "hashicorp"
    with patch("smk.core.web.routes.migrate.ConfigManager") as mock_cm:
        mock_cm.return_value.load.return_value = mock_cfg
        result = _get_source_plugin()
    assert result == "hashicorp"


def test_load_source_entities_missing_file(tmp_path: Path) -> None:
    """_load_source_entities returns [] when file missing."""
    from smk.core.web.routes.migrate import _load_source_entities

    with patch("smk.core.web.routes.migrate.get_data_dir", return_value=tmp_path / "nonexistent"):
        result = _load_source_entities("workspaces")
    assert result == []


def test_load_source_entities_reads_file(tmp_path: Path) -> None:
    """_load_source_entities reads JSON from file."""
    import json as _json

    from smk.core.web.routes.migrate import _load_source_entities

    data = [{"id": "ws-1", "name": "test"}]
    src_dir = tmp_path / "source"
    src_dir.mkdir(parents=True)
    (src_dir / "workspaces.json").write_text(_json.dumps(data))
    with patch("smk.core.web.routes.migrate.get_data_dir", return_value=src_dir):
        result = _load_source_entities("workspaces")
    assert result == data


def test_get_db_uses_config_dir_from_state(tmp_path: Path) -> None:
    """_get_db picks up config_dir from request.app.state.web_config."""
    from unittest.mock import MagicMock

    from smk.core.web.routes.migrate import _get_db

    config_stub = MagicMock()
    config_stub.config_dir = tmp_path
    request = MagicMock()
    request.app.state.web_config = config_stub
    conn = _get_db(request)
    assert (tmp_path / "smk.db").exists()
    conn.close()


def test_start_transform_success(db_client, tmp_path: Path) -> None:
    """POST /api/migrate/batch/{id}/transform runs transform."""
    client, tmp_path = db_client
    from smk.core.db import get_db
    from smk.core.db.batches import create_batch

    db = get_db(tmp_path)
    batch = create_batch(db)
    db.close()

    mock_pm = MagicMock()
    with (
        patch("smk.core.web.routes.migrate._get_source_plugin", return_value="hashicorp"),
    ):
        client.app.state.plugin_manager = mock_pm
        response = client.post(f"/api/migrate/batch/{batch['id']}/transform")
    assert response.status_code == 200
    mock_pm.transform_batch.assert_called_once()


def test_confirm_batch_not_found(db_client) -> None:
    """POST /api/migrate/batch/999/confirm returns 404."""
    client, _ = db_client
    response = client.post("/api/migrate/batch/999/confirm")
    assert response.status_code == 404


def test_confirm_batch_not_draft(db_client, tmp_path: Path) -> None:
    """POST /api/migrate/batch/{id}/confirm returns 400 for confirmed batch."""
    client, tmp_path = db_client
    from smk.core.db import get_db
    from smk.core.db.batches import confirm_batch, create_batch

    db = get_db(tmp_path)
    batch = create_batch(db)
    db.execute(
        _SQL_ORG_READY,
        (batch["id"],),
    )
    db.commit()
    confirm_batch(db, batch["id"])
    db.close()

    response = client.post(f"/api/migrate/batch/{batch['id']}/confirm")
    assert response.status_code == 400


def test_confirm_batch_no_ready_entities(db_client, tmp_path: Path) -> None:
    """POST /api/migrate/batch/{id}/confirm returns 400 when no ready entities."""
    client, tmp_path = db_client
    from smk.core.db import get_db
    from smk.core.db.batches import create_batch

    db = get_db(tmp_path)
    batch = create_batch(db)
    db.close()

    response = client.post(f"/api/migrate/batch/{batch['id']}/confirm")
    assert response.status_code == 400


def test_confirm_batch_writes_hcl(db_client, tmp_path: Path) -> None:
    """POST /api/migrate/batch/{id}/confirm writes HCL file."""
    client, tmp_path = db_client
    from smk.core.db import get_db
    from smk.core.db.batches import create_batch

    spacelift_entity = json.dumps(
        {
            "resource_type": "spacelift_space",
            "resource_name": "org_test",
            "attributes": {"name": "test", "parent_space_id": "root"},
        }
    )

    db = get_db(tmp_path)
    batch = create_batch(db)
    db.execute(
        """INSERT INTO batch_entities
           (batch_id, entity_type, entity_id, entity_name, status, spacelift_entity)
           VALUES (?, 'organizations', 'org-1', 'test', 'ready', ?)""",
        (batch["id"], spacelift_entity),
    )
    db.commit()
    db.close()

    output_dir = tmp_path / "output"

    with patch("smk.core.web.routes.migrate.get_output_dir", return_value=output_dir):
        response = client.post(f"/api/migrate/batch/{batch['id']}/confirm")

    assert response.status_code == 200
    data = response.json()
    assert data["entity_count"] == 1
    assert data["batch_id"] == batch["id"]
    assert Path(data["hcl_path"]).exists()
