"""Tests for plugin manager."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from smk.core.plugins.manager import SMKPluginManager


@pytest.fixture
def mock_plugins_dir(tmp_path: Path) -> Path:
    """Create temporary plugins directory."""
    plugins_dir = tmp_path / "plugins"
    plugins_dir.mkdir()
    return plugins_dir


def test_plugin_manager_init():
    """Test plugin manager initialization."""
    manager = SMKPluginManager()

    assert manager.pm is not None
    assert manager.cache is not None
    assert manager.dep_manager is not None
    assert manager.loader is not None
    assert manager.loaded_plugins == {}
    assert manager.failed_plugins == {}


def test_detect_bundled_mode_false_in_development():
    """Test bundled mode detection in development."""
    manager = SMKPluginManager()
    assert manager.is_bundled is False


def test_detect_bundled_mode_true_when_frozen():
    """Test bundled mode detection when frozen."""
    import sys

    # Temporarily set frozen attribute using setattr to avoid type error
    sys.frozen = True  # type: ignore[attr-defined]
    try:
        manager = SMKPluginManager()
        assert manager.is_bundled is True
    finally:
        if hasattr(sys, "frozen"):
            delattr(sys, "frozen")


def test_initialize_loads_plugins():
    """Test initialize loads both builtin and third-party plugins."""
    with (
        patch.object(SMKPluginManager, "_load_builtin_plugins") as mock_builtin,
        patch.object(SMKPluginManager, "_load_third_party_plugins") as mock_third_party,
    ):
        manager = SMKPluginManager()
        manager.initialize()

        mock_builtin.assert_called_once()
        mock_third_party.assert_called_once()


def test_get_loaded_plugins_returns_copy():
    """Test get_loaded_plugins returns copy of dict."""
    manager = SMKPluginManager()
    manager.loaded_plugins = {"test": MagicMock()}

    result = manager.get_loaded_plugins()

    assert result == manager.loaded_plugins
    assert result is not manager.loaded_plugins


def test_get_failed_plugins_returns_copy():
    """Test get_failed_plugins returns copy of dict."""
    manager = SMKPluginManager()
    manager.failed_plugins = {"test": "error message"}

    result = manager.get_failed_plugins()

    assert result == manager.failed_plugins
    assert result is not manager.failed_plugins


def test_is_development_mode():
    """Test development mode check."""
    manager = SMKPluginManager()
    # Should be True in tests (not frozen)
    assert manager.is_development_mode() is True
