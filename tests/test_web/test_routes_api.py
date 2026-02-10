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
