"""Tests for API routes."""

from pathlib import Path

from fastapi.testclient import TestClient


def test_health_returns_ok(client: TestClient) -> None:
    """Health check returns status ok."""
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_config_status_returns_200(client: TestClient) -> None:
    """Config status endpoint returns 200 OK."""
    response = client.get("/api/config/status")
    assert response.status_code == 200
    data = response.json()
    assert "config_file" in data
    assert "initialized" in data


def test_config_returns_200(client: TestClient) -> None:
    """Config endpoint returns 200 OK."""
    response = client.get("/api/config")
    assert response.status_code == 200


def test_get_source_plugins_returns_list(client: TestClient) -> None:
    """Source plugins endpoint returns a list with hashicorp and spacelift."""
    response = client.get("/api/plugins/sources")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    plugin_ids = [p["plugin_id"] for p in data]
    assert "hashicorp" in plugin_ids
    assert "spacelift" in plugin_ids


def test_post_export_returns_counts(client: TestClient) -> None:
    """POST /api/export returns entity counts from the source plugin."""
    from unittest.mock import MagicMock, patch

    mock_config = MagicMock()
    mock_config.source.credentials = {"token": "t"}
    export_result = {"organizations": 2, "projects": 5, "workspaces": 10}

    with (
        patch("smk.core.web.routes.api.ConfigManager") as mock_cm,
        patch("smk.core.web.routes.api.asyncio.to_thread") as mock_thread,
    ):
        mock_cm.return_value.load.return_value = mock_config
        mock_thread.return_value = [export_result]
        response = client.post("/api/export")

    assert response.status_code == 200
    assert response.json() == export_result


def test_post_export_returns_400_when_config_not_initialized(client: TestClient) -> None:
    """POST /api/export returns 400 when configuration is not initialized."""
    from unittest.mock import patch

    from smk.core.exceptions import ConfigNotInitializedError

    with patch("smk.core.web.routes.api.ConfigManager") as mock_cm:
        mock_cm.return_value.load.side_effect = ConfigNotInitializedError
        response = client.post("/api/export")

    assert response.status_code == 400
    assert response.json()["detail"] == "Configuration not initialized"


def test_post_export_returns_502_on_plugin_error(client: TestClient) -> None:
    """POST /api/export returns 502 when the plugin raises an exception."""
    from unittest.mock import MagicMock, patch

    mock_config = MagicMock()
    mock_config.source.credentials = {"token": "bad"}

    with (
        patch("smk.core.web.routes.api.ConfigManager") as mock_cm,
        patch("smk.core.web.routes.api.asyncio.to_thread") as mock_thread,
    ):
        mock_cm.return_value.load.return_value = mock_config
        mock_thread.side_effect = RuntimeError("unauthorized")
        response = client.post("/api/export")

    assert response.status_code == 502
    assert "unauthorized" in response.json()["detail"]


def test_export_status_not_exported_when_not_initialized(client: TestClient) -> None:
    """GET /api/export/status returns exported: false when config is not initialized."""
    from unittest.mock import patch

    with patch("smk.core.web.routes.api.ConfigManager") as mock_cm:
        mock_cm.return_value.is_initialized = False
        response = client.get("/api/export/status")

    assert response.status_code == 200
    assert response.json() == {"exported": False}


def test_export_status_not_exported_when_load_raises(client: TestClient) -> None:
    """GET /api/export/status returns exported: false when config load raises."""
    from unittest.mock import patch

    from smk.core.exceptions import ConfigNotInitializedError

    with patch("smk.core.web.routes.api.ConfigManager") as mock_cm:
        mock_cm.return_value.is_initialized = True
        mock_cm.return_value.load.side_effect = ConfigNotInitializedError
        response = client.get("/api/export/status")

    assert response.status_code == 200
    assert response.json() == {"exported": False}


def test_export_status_not_exported(client: TestClient, tmp_path: Path) -> None:
    """GET /api/export/status returns exported: false when source files are missing."""
    from unittest.mock import MagicMock, patch

    mock_config = MagicMock()
    mock_config.source.plugin = "hashicorp"
    entity_types = [
        {"id": "organizations", "display_name": "Organizations"},
        {"id": "projects", "display_name": "Projects"},
        {"id": "workspaces", "display_name": "Workspaces"},
    ]

    with (
        patch("smk.core.web.routes.api.ConfigManager") as mock_cm,
        patch("smk.core.web.routes.api.get_data_dir", return_value=tmp_path),
        patch.object(client.app.state.plugin_manager, "get_entity_types", return_value=entity_types),
    ):
        mock_cm.return_value.is_initialized = True
        mock_cm.return_value.load.return_value = mock_config
        response = client.get("/api/export/status")

    assert response.status_code == 200
    assert response.json() == {"exported": False}


def test_export_status_exported(client: TestClient, tmp_path: Path) -> None:
    """GET /api/export/status returns exported: true with counts when source files exist."""
    from unittest.mock import MagicMock, patch

    import orjson

    (tmp_path / "organizations.json").write_bytes(orjson.dumps([{"id": 1}, {"id": 2}]))
    (tmp_path / "projects.json").write_bytes(orjson.dumps([{"id": 1}]))
    (tmp_path / "workspaces.json").write_bytes(orjson.dumps([{"id": 1}, {"id": 2}, {"id": 3}]))

    mock_config = MagicMock()
    mock_config.source.plugin = "hashicorp"
    entity_types = [
        {"id": "organizations", "display_name": "Organizations"},
        {"id": "projects", "display_name": "Projects"},
        {"id": "workspaces", "display_name": "Workspaces"},
    ]

    with (
        patch("smk.core.web.routes.api.ConfigManager") as mock_cm,
        patch("smk.core.web.routes.api.get_data_dir", return_value=tmp_path),
        patch.object(client.app.state.plugin_manager, "get_entity_types", return_value=entity_types),
    ):
        mock_cm.return_value.is_initialized = True
        mock_cm.return_value.load.return_value = mock_config
        response = client.get("/api/export/status")

    assert response.status_code == 200
    assert response.json() == {
        "exported": True,
        "organizations": 2,
        "projects": 1,
        "workspaces": 3,
    }


def test_get_entity_types_returns_list(client: TestClient) -> None:
    """GET /api/entity-types returns entity types for configured plugin."""
    from unittest.mock import MagicMock, patch

    mock_config = MagicMock()
    mock_config.source.plugin = "hashicorp"
    entity_types = [{"id": "workspaces", "display_name": "Workspaces"}]

    with (
        patch("smk.core.web.routes.api.ConfigManager") as mock_cm,
        patch.object(client.app.state.plugin_manager, "get_entity_types", return_value=entity_types),
    ):
        mock_cm.return_value.load.return_value = mock_config
        response = client.get("/api/entity-types")

    assert response.status_code == 200
    assert response.json() == entity_types


def test_get_entity_types_returns_empty_when_not_initialized(client: TestClient) -> None:
    """GET /api/entity-types returns empty list when config is not initialized."""
    from unittest.mock import patch

    from smk.core.exceptions import ConfigNotInitializedError

    with patch("smk.core.web.routes.api.ConfigManager") as mock_cm:
        mock_cm.return_value.load.side_effect = ConfigNotInitializedError
        response = client.get("/api/entity-types")

    assert response.status_code == 200
    assert response.json() == []


def test_post_audit_returns_results(client: TestClient) -> None:
    """POST /api/audit runs audit and returns entity types + issues."""
    from unittest.mock import MagicMock, patch

    mock_config = MagicMock()
    mock_config.source.plugin = "hashicorp"
    entity_types = [{"id": "workspaces", "display_name": "Workspaces"}]
    audit_results = {"workspaces": [{"entity_id": "ws-1", "severity": "warning", "message": "No VCS configuration"}]}

    with (
        patch("smk.core.web.routes.api.ConfigManager") as mock_cm,
        patch("smk.core.web.routes.api.get_data_dir") as mock_data_dir,
        patch.object(client.app.state.plugin_manager, "get_entity_types", return_value=entity_types),
        patch("smk.core.web.routes.api.asyncio.to_thread") as mock_thread,
    ):
        mock_cm.return_value.load.return_value = mock_config
        mock_data_dir.return_value = MagicMock()
        mock_thread.return_value = audit_results
        response = client.post("/api/audit")

    assert response.status_code == 200
    data = response.json()
    assert data["entity_types"] == entity_types
    assert data["issues"] == audit_results


def test_post_audit_returns_400_when_not_initialized(client: TestClient) -> None:
    """POST /api/audit returns 400 when configuration not initialized."""
    from unittest.mock import patch

    from smk.core.exceptions import ConfigNotInitializedError

    with patch("smk.core.web.routes.api.ConfigManager") as mock_cm:
        mock_cm.return_value.load.side_effect = ConfigNotInitializedError
        response = client.post("/api/audit")

    assert response.status_code == 400
    assert response.json()["detail"] == "Configuration not initialized"


def test_post_audit_returns_502_on_error(client: TestClient) -> None:
    """POST /api/audit returns 502 when audit raises an exception."""
    from unittest.mock import MagicMock, patch

    mock_config = MagicMock()
    mock_config.source.plugin = "hashicorp"
    entity_types = [{"id": "workspaces", "display_name": "Workspaces"}]

    with (
        patch("smk.core.web.routes.api.ConfigManager") as mock_cm,
        patch.object(client.app.state.plugin_manager, "get_entity_types", return_value=entity_types),
        patch("smk.core.web.routes.api.asyncio.to_thread") as mock_thread,
    ):
        mock_cm.return_value.load.return_value = mock_config
        mock_thread.side_effect = RuntimeError("disk error")
        response = client.post("/api/audit")

    assert response.status_code == 502
    assert "disk error" in response.json()["detail"]


def test_audit_status_not_audited(client: TestClient, tmp_path: Path) -> None:
    """GET /api/audit/status returns audited: false when results file is missing."""
    from unittest.mock import patch

    with patch("smk.core.web.routes.api.get_data_dir", return_value=tmp_path):
        response = client.get("/api/audit/status")

    assert response.status_code == 200
    assert response.json() == {"audited": False}


def test_audit_status_returns_cached_results(client: TestClient, tmp_path: Path) -> None:
    """GET /api/audit/status returns cached results when file exists."""
    from unittest.mock import MagicMock, patch

    import orjson

    issues = {"workspaces": [{"entity_id": "ws-1", "severity": "warning", "message": "No VCS configuration"}]}
    (tmp_path / "audit_results.json").write_bytes(orjson.dumps(issues))

    mock_config = MagicMock()
    mock_config.source.plugin = "hashicorp"
    entity_types = [{"id": "workspaces", "display_name": "Workspaces"}]

    with (
        patch("smk.core.web.routes.api.ConfigManager") as mock_cm,
        patch("smk.core.web.routes.api.get_data_dir", return_value=tmp_path),
        patch.object(client.app.state.plugin_manager, "get_entity_types", return_value=entity_types),
    ):
        mock_cm.return_value.load.return_value = mock_config
        response = client.get("/api/audit/status")

    assert response.status_code == 200
    data = response.json()
    assert data["audited"] is True
    assert data["entity_types"] == entity_types
    assert data["issues"] == issues


def test_audit_status_not_audited_when_config_not_initialized(client: TestClient, tmp_path: Path) -> None:
    """GET /api/audit/status returns audited: false when config not initialized."""
    from unittest.mock import patch

    import orjson

    from smk.core.exceptions import ConfigNotInitializedError

    (tmp_path / "audit_results.json").write_bytes(orjson.dumps({}))

    with (
        patch("smk.core.web.routes.api.ConfigManager") as mock_cm,
        patch("smk.core.web.routes.api.get_data_dir", return_value=tmp_path),
    ):
        mock_cm.return_value.load.side_effect = ConfigNotInitializedError
        response = client.get("/api/audit/status")

    assert response.status_code == 200
    assert response.json() == {"audited": False}


def test_get_config_returns_error_when_not_initialized(client: TestClient) -> None:
    """GET /api/config returns error dict when config is not initialized."""
    from unittest.mock import patch

    from smk.core.exceptions import ConfigNotInitializedError

    with patch("smk.core.web.routes.api.ConfigManager") as mock_cm:
        mock_cm.return_value.load.side_effect = ConfigNotInitializedError
        response = client.get("/api/config")

    assert response.status_code == 200
    assert response.json() == {"error": "Configuration not initialized"}


def test_post_config_saves_successfully(client: TestClient) -> None:
    """POST /api/config saves configuration and returns status saved."""
    from unittest.mock import MagicMock, patch

    mock_config = MagicMock()
    with patch("smk.core.web.routes.api.ConfigManager") as mock_cm:
        mock_cm.return_value.init.return_value = mock_config
        response = client.post(
            "/api/config",
            json={
                "source_plugin": "hashicorp",
                "source_credentials": {"product": "hcp_terraform", "token": "test-token"},
                "spacelift_api_endpoint": "https://example.app.spacelift.io",
                "spacelift_api_key_id": "key-id",
                "spacelift_api_key_secret": "key-secret",
            },
        )
    assert response.status_code == 200
    assert response.json() == {"status": "saved"}
    mock_cm.return_value.init.assert_called_once_with(
        force=True,
        source_credentials={"product": "hcp_terraform", "token": "test-token"},
        source_plugin="hashicorp",
        spacelift_endpoint="https://example.app.spacelift.io",
        spacelift_key_id="key-id",
        spacelift_key_secret="key-secret",
    )
