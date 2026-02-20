"""Tests for API routes."""

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
