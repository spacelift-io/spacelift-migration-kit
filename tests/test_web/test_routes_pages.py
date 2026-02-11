"""Tests for page routes."""

from fastapi.testclient import TestClient


def test_homepage_returns_200(client: TestClient) -> None:
    """Homepage returns 200 OK."""
    response = client.get("/")
    assert response.status_code == 200


def test_homepage_is_workflow_start(client: TestClient) -> None:
    """Homepage is the workflow start page."""
    response = client.get("/")
    assert "Welcome to Spacelift Migration Kit" in response.text
