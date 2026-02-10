"""Tests for page routes."""

from fastapi.testclient import TestClient


def test_dashboard_returns_200(client: TestClient) -> None:
    """Dashboard page returns 200 OK."""
    response = client.get("/")
    assert response.status_code == 200


def test_dashboard_contains_title(client: TestClient) -> None:
    """Dashboard page contains expected title."""
    response = client.get("/")
    assert "Dashboard" in response.text


def test_config_page_returns_200(client: TestClient) -> None:
    """Config page returns 200 OK."""
    response = client.get("/config")
    assert response.status_code == 200


def test_config_page_contains_title(client: TestClient) -> None:
    """Config page contains expected title."""
    response = client.get("/config")
    assert "Configuration" in response.text
