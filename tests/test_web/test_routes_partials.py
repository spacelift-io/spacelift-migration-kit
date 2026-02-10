"""Tests for partial routes."""

from fastapi.testclient import TestClient


def test_config_status_partial_returns_200(client: TestClient) -> None:
    """Config status partial returns 200 OK."""
    response = client.get("/partials/config-status")
    assert response.status_code == 200


def test_config_status_partial_contains_status(client: TestClient) -> None:
    """Config status partial contains status information."""
    response = client.get("/partials/config-status")
    # Should contain either "initialized" or "Not initialized"
    assert "initialized" in response.text.lower()
