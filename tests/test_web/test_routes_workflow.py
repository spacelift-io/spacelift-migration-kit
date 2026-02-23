"""Tests for workflow routes."""

import pytest
from fastapi.testclient import TestClient

from smk.core.config.manager import ConfigManager
from smk.core.web.app import create_app


@pytest.fixture
def client() -> TestClient:
    """Create test client."""
    app = create_app()
    return TestClient(app)


def test_workflow_start(client: TestClient) -> None:
    """Test workflow start page."""
    response = client.get("/start")
    assert response.status_code == 200
    assert b"Welcome to Spacelift Migration Kit" in response.content
    assert b"Get Started" in response.content


def test_workflow_start_as_homepage(client: TestClient) -> None:
    """Test workflow start page is accessible at root."""
    response = client.get("/")
    assert response.status_code == 200
    assert b"Welcome to Spacelift Migration Kit" in response.content


def test_workflow_configure(client: TestClient) -> None:
    """Test workflow configure page shows dynamic plugin list."""
    response = client.get("/configure")
    assert response.status_code == 200
    assert b"Configure SMK" in response.content
    assert b"Source Configuration" in response.content
    assert b"Destination Spacelift Configuration" in response.content
    # Dynamic plugins present
    assert b"HashiCorp" in response.content
    assert b"Spacelift" in response.content
    # No hardcoded static <option> entries from old implementation
    assert b"<option>Terraform Cloud</option>" not in response.content
    assert b"<option>GitLab CI</option>" not in response.content


def test_workflow_export(client: TestClient) -> None:
    """Test workflow export page."""
    response = client.get("/export")
    assert response.status_code == 200
    assert b"Export Source Data" in response.content
    assert b"Export Progress" in response.content
    assert b"Start Export" in response.content


def test_workflow_audit(client: TestClient) -> None:
    """Test workflow audit page."""
    response = client.get("/audit")
    assert response.status_code == 200
    assert b"Audit Source Data" in response.content
    assert b"Audit Results" in response.content
    assert b"Workspaces" in response.content


def test_workflow_migrate(client: TestClient) -> None:
    """Test workflow migrate page."""
    response = client.get("/migrate")
    assert response.status_code == 200
    assert b"Migrate Resources" in response.content
    assert b"Batch 1 of 5" in response.content
    assert b"Migration Progress" in response.content


def test_workflow_cleanup(client: TestClient) -> None:
    """Test workflow cleanup page."""
    response = client.get("/cleanup")
    assert response.status_code == 200
    assert b"Post-Migration Cleanup" in response.content
    assert b"Archive old workspaces" in response.content
    assert b"Update CI/CD pipelines" in response.content


def test_workflow_complete(client: TestClient) -> None:
    """Test workflow complete page."""
    response = client.get("/complete")
    assert response.status_code == 200
    assert b"Migration Complete!" in response.content
    assert b"Migration Summary" in response.content
    assert b"Settings" in response.content


def test_workflow_stepper_on_start(client: TestClient) -> None:
    """Test stepper shows correct state on start page."""
    response = client.get("/start")
    content = response.content.decode()
    # Stepper should be present
    assert "Start" in content
    assert "Configure" in content
    assert "Wrap Up" in content


def test_workflow_stepper_on_middle_step(client: TestClient) -> None:
    """Test stepper shows correct state on middle step."""
    response = client.get("/audit")
    content = response.content.decode()
    # All step names should be present in stepper
    assert "Start" in content
    assert "Audit" in content
    assert "Migrate" in content


def test_workflow_navigation_links(client: TestClient) -> None:
    """Test navigation links between workflow steps."""
    # Start page should only have next link
    response = client.get("/start")
    assert b"/configure" in response.content

    # Middle pages should have both prev and next
    response = client.get("/configure")
    assert b"/start" in response.content
    assert b"/export" in response.content

    # Complete page should link to start
    response = client.get("/complete")
    assert b"/start" in response.content


def test_workflow_root_redirects_to_last_step(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test / redirects to last visited step when state exists."""
    monkeypatch.setattr(ConfigManager, "load_last_step", lambda _self: "export")
    response = client.get("/", follow_redirects=False)
    assert response.status_code in (302, 307)
    assert response.headers["location"] == "/export"


def test_workflow_root_shows_start_when_no_state(client: TestClient) -> None:
    """Test / shows start page when no prior state (autouse returns 'start')."""
    response = client.get("/")
    assert response.status_code == 200
    assert b"Welcome to Spacelift Migration Kit" in response.content


def test_workflow_start_shows_resume_cta(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test /start shows resume CTA when prior step exists."""
    monkeypatch.setattr(ConfigManager, "load_last_step", lambda _self: "export")
    response = client.get("/start")
    assert response.status_code == 200
    assert b"Continue Migration" in response.content
    assert b"Export" in response.content
    assert b"Start from the beginning" in response.content


def test_workflow_context_helper() -> None:
    """Test _get_workflow_context helper function."""
    from smk.core.web.routes.workflow import _get_workflow_context

    # Test start step
    context = _get_workflow_context("start")
    assert context["current_step"] == "start"
    assert context["completed_steps"] == []
    assert context["prev_step"] is None
    assert context["next_step"] == "configure"

    # Test middle step
    context = _get_workflow_context("audit")
    assert context["current_step"] == "audit"
    assert context["completed_steps"] == ["start", "configure", "export"]
    assert context["prev_step"] == "export"
    assert context["next_step"] == "migrate"

    # Test last step
    context = _get_workflow_context("complete")
    assert context["current_step"] == "complete"
    assert context["completed_steps"] == [
        "start",
        "configure",
        "export",
        "audit",
        "migrate",
        "cleanup",
    ]
    assert context["prev_step"] == "cleanup"
    assert context["next_step"] is None
