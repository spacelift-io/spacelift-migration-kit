"""Tests for the TUI application."""

import pytest

from smk.core.tui import TUIApp
from smk.core.tui.app import WelcomeMessage, _get_version


@pytest.mark.asyncio
async def test_tui_app_launches():
    """Test that the TUI app launches and renders."""
    app = TUIApp()
    async with app.run_test() as pilot:
        assert app.title == "SMK - Spacelift Migration Kit"
        assert pilot.app is app


@pytest.mark.asyncio
async def test_tui_app_has_welcome_message():
    """Test that the TUI displays a welcome message."""
    app = TUIApp()
    async with app.run_test():
        welcome = app.query_one(WelcomeMessage)
        # WelcomeMessage is a Static widget; check its render output
        assert "Welcome to SMK" in str(welcome.render())


@pytest.mark.asyncio
async def test_tui_app_quit_binding():
    """Test that q quits the app."""
    app = TUIApp()
    async with app.run_test() as pilot:
        await pilot.press("q")
        assert app._exit


@pytest.mark.asyncio
async def test_tui_app_help_binding():
    """Test that ? shows help notification."""
    app = TUIApp()
    async with app.run_test() as pilot:
        await pilot.press("?")
        # Help should trigger a notification
        assert len(app._notifications) > 0


def test_get_version_returns_string():
    """Test that _get_version returns a string."""
    version = _get_version()
    assert isinstance(version, str)
    assert len(version) > 0
