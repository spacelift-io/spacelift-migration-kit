"""Tests for FastAPI application factory."""

from smk.core.web.app import create_app
from smk.core.web.config import WebConfig


def test_create_app_with_none_config() -> None:
    """create_app uses WebConfig defaults when called with no args."""
    app = create_app(None)
    assert app.state.config == WebConfig()


def test_create_app_hot_reload_not_set_when_debug_false() -> None:
    """create_app sets hot_reload to None when debug=False."""
    config = WebConfig(debug=False, open_browser=False)
    app = create_app(config)
    assert app.state.hot_reload is None
