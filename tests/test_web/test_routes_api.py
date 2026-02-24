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


def test_export_status_not_exported(client: TestClient, tmp_path: Path) -> None:
    """GET /api/export/status returns exported: false when source files are missing."""
    from unittest.mock import patch

    with patch("smk.core.web.routes.api.get_data_dir", return_value=tmp_path):
        response = client.get("/api/export/status")

    assert response.status_code == 200
    assert response.json() == {"exported": False}


def test_export_status_exported(client: TestClient, tmp_path: Path) -> None:
    """GET /api/export/status returns exported: true with counts when source files exist."""
    from unittest.mock import patch

    import orjson

    (tmp_path / "organizations.json").write_bytes(orjson.dumps([{"id": 1}, {"id": 2}]))
    (tmp_path / "projects.json").write_bytes(orjson.dumps([{"id": 1}]))
    (tmp_path / "workspaces.json").write_bytes(orjson.dumps([{"id": 1}, {"id": 2}, {"id": 3}]))

    with patch("smk.core.web.routes.api.get_data_dir", return_value=tmp_path):
        response = client.get("/api/export/status")

    assert response.status_code == 200
    assert response.json() == {
        "exported": True,
        "organizations": 2,
        "projects": 1,
        "workspaces": 3,
    }


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
