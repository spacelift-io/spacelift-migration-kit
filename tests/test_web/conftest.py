"""Web test fixtures."""

import pytest
from fastapi.testclient import TestClient

from smk.core.config.manager import ConfigManager
from smk.core.web.app import create_app
from smk.core.web.config import WebConfig


@pytest.fixture(autouse=True)
def isolated_state(monkeypatch: pytest.MonkeyPatch) -> None:
    """Prevent tests from reading/writing the real state.yaml."""
    monkeypatch.setattr(ConfigManager, "load_last_step", lambda _self: "start")
    monkeypatch.setattr(ConfigManager, "save_last_step", lambda _self, _step: None)


@pytest.fixture
def web_config() -> WebConfig:
    """Create a test web config."""
    return WebConfig(debug=True, open_browser=False)


@pytest.fixture
def client(web_config: WebConfig) -> TestClient:
    """Create a test client for the web app."""
    app = create_app(web_config)
    return TestClient(app)
