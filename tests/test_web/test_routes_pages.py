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


def test_plugins_page_returns_200(client: TestClient) -> None:
    """Plugins page returns 200 OK."""
    response = client.get("/plugins")
    assert response.status_code == 200


def test_plugins_page_contains_title(client: TestClient) -> None:
    """Plugins page contains expected title."""
    response = client.get("/plugins")
    assert "Plugin Management" in response.text


def test_plugins_page_shows_deployment_mode(client: TestClient) -> None:
    """Plugins page shows deployment mode information."""
    response = client.get("/plugins")
    assert "Deployment Mode" in response.text
    # In tests, should be development mode
    assert "Development Mode" in response.text
