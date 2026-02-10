"""Tests for desktop launcher."""

from unittest.mock import Mock, patch


def test_is_desktop_available_with_pywebview() -> None:
    """Test is_desktop_available returns True when pywebview is available."""
    from smk.core.desktop.launcher import is_desktop_available

    with patch.dict("sys.modules", {"webview": Mock()}):
        assert is_desktop_available() is True


def test_is_desktop_available_returns_bool() -> None:
    """Test is_desktop_available returns a boolean value."""
    from smk.core.desktop.launcher import is_desktop_available

    result = is_desktop_available()
    assert isinstance(result, bool)
