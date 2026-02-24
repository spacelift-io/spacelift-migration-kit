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


def test_load_builtin_plugins_records_failure() -> None:
    """_load_builtin_plugins adds to failed_plugins when pm.register raises."""
    manager = SMKPluginManager()

    fake_module = MagicMock()
    fake_module.__name__ = "bad_plugin"

    with (
        patch.object(manager.loader, "discover_builtin_plugins", return_value=[fake_module]),
        patch.object(manager.pm, "register", side_effect=RuntimeError("conflict")),
    ):
        manager._load_builtin_plugins()

    assert "bad_plugin" in manager.failed_plugins


def test_load_plugin_success(tmp_path: Path) -> None:
    """_load_plugin adds plugin to loaded_plugins on success."""
    plugin_file = tmp_path / "myplugin.py"
    plugin_file.write_text("# empty plugin\n")

    manager = SMKPluginManager()

    with (
        patch.object(manager.dep_manager, "handle_dependencies", return_value=(True, None)),
        patch.object(manager.pm, "register"),
    ):
        manager._load_plugin(plugin_file)

    assert "myplugin" in manager.loaded_plugins


def test_load_plugin_dep_failure(tmp_path: Path) -> None:
    """_load_plugin adds to failed_plugins when dependency check fails."""
    plugin_file = tmp_path / "badplugin.py"
    plugin_file.write_text("")

    manager = SMKPluginManager()

    with patch.object(manager.dep_manager, "handle_dependencies", return_value=(False, "missing dep")):
        manager._load_plugin(plugin_file)

    assert "badplugin" in manager.failed_plugins
    assert manager.failed_plugins["badplugin"] == "missing dep"


def test_load_plugin_exception(tmp_path: Path) -> None:
    """_load_plugin adds to failed_plugins when load_plugin_module raises."""
    plugin_file = tmp_path / "errplugin.py"
    plugin_file.write_text("")

    manager = SMKPluginManager()

    with (
        patch.object(manager.dep_manager, "handle_dependencies", return_value=(True, None)),
        patch.object(manager.loader, "load_plugin_module", side_effect=ImportError("bad import")),
    ):
        manager._load_plugin(plugin_file)

    assert "errplugin" in manager.failed_plugins


def test_load_third_party_plugins_calls_load_plugin(tmp_path: Path) -> None:
    """_load_third_party_plugins calls _load_plugin for each discovered plugin."""
    plugin_file = tmp_path / "myplugin.py"
    plugin_file.write_text("")

    manager = SMKPluginManager()

    with (
        patch.object(manager.loader, "discover_third_party_plugins", return_value=[plugin_file]),
        patch.object(manager, "_load_plugin") as mock_load,
    ):
        manager._load_third_party_plugins()

    mock_load.assert_called_once_with(plugin_file)


def test_get_source_plugins_filters_none() -> None:
    """get_source_plugins excludes None results from hook calls."""
    manager = SMKPluginManager()

    with patch.object(manager.pm.hook, "smk_get_source_info", return_value=[None, {"plugin_id": "x"}]):
        plugins = manager.get_source_plugins()

    assert len(plugins) == 1
    assert plugins[0]["plugin_id"] == "x"
