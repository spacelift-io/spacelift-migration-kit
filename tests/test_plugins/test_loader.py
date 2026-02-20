"""Tests for plugin loader."""

from pathlib import Path

import pytest

from smk.core.plugins.loader import PluginLoader


@pytest.fixture
def temp_plugins_dir(tmp_path: Path) -> Path:
    """Create temporary plugins directory."""
    plugins_dir = tmp_path / "plugins"
    plugins_dir.mkdir()
    return plugins_dir


def test_discover_builtin_plugins_returns_hashicorp_and_spacelift():
    """Test builtin plugin discovery returns hashicorp and spacelift modules."""
    loader = PluginLoader()
    plugins = loader.discover_builtin_plugins()
    plugin_names = [getattr(p, "__name__", "") for p in plugins]
    assert any("hashicorp" in name for name in plugin_names)
    assert any("spacelift" in name for name in plugin_names)


def test_discover_third_party_plugins_empty_directory(temp_plugins_dir: Path):
    """Test discovery in empty directory."""
    loader = PluginLoader()
    loader.plugins_dir = temp_plugins_dir

    plugins = loader.discover_third_party_plugins()
    assert plugins == []


def test_discover_third_party_plugins_nonexistent_directory(tmp_path: Path):
    """Test discovery when directory doesn't exist."""
    loader = PluginLoader()
    loader.plugins_dir = tmp_path / "nonexistent"

    plugins = loader.discover_third_party_plugins()
    assert plugins == []


def test_discover_third_party_plugins_finds_py_files(temp_plugins_dir: Path):
    """Test discovery finds .py files."""
    # Create a plugin file
    plugin_file = temp_plugins_dir / "test_plugin.py"
    plugin_file.write_text("# test plugin")

    loader = PluginLoader()
    loader.plugins_dir = temp_plugins_dir

    plugins = loader.discover_third_party_plugins()
    assert len(plugins) == 1
    assert plugins[0] == plugin_file


def test_discover_third_party_plugins_ignores_init_py(temp_plugins_dir: Path):
    """Test discovery ignores __init__.py."""
    # Create __init__.py
    init_file = temp_plugins_dir / "__init__.py"
    init_file.write_text("")

    loader = PluginLoader()
    loader.plugins_dir = temp_plugins_dir

    plugins = loader.discover_third_party_plugins()
    assert len(plugins) == 0


def test_discover_third_party_plugins_finds_directories(temp_plugins_dir: Path):
    """Test discovery finds directories with __init__.py."""
    # Create a plugin directory
    plugin_dir = temp_plugins_dir / "test_plugin"
    plugin_dir.mkdir()
    (plugin_dir / "__init__.py").write_text("")

    loader = PluginLoader()
    loader.plugins_dir = temp_plugins_dir

    plugins = loader.discover_third_party_plugins()
    assert len(plugins) == 1
    assert plugins[0] == plugin_dir


def test_discover_third_party_plugins_ignores_dir_without_init(temp_plugins_dir: Path):
    """Test discovery ignores directories without __init__.py."""
    # Create a directory without __init__.py
    not_plugin_dir = temp_plugins_dir / "not_plugin"
    not_plugin_dir.mkdir()

    loader = PluginLoader()
    loader.plugins_dir = temp_plugins_dir

    plugins = loader.discover_third_party_plugins()
    assert len(plugins) == 0


def test_discover_third_party_plugins_sorts_results(temp_plugins_dir: Path):
    """Test discovery returns sorted results."""
    # Create multiple plugins
    (temp_plugins_dir / "z_plugin.py").write_text("")
    (temp_plugins_dir / "a_plugin.py").write_text("")
    plugin_dir = temp_plugins_dir / "m_plugin"
    plugin_dir.mkdir()
    (plugin_dir / "__init__.py").write_text("")

    loader = PluginLoader()
    loader.plugins_dir = temp_plugins_dir

    plugins = loader.discover_third_party_plugins()
    names = [p.name for p in plugins]
    assert names == ["a_plugin.py", "m_plugin", "z_plugin.py"]


def test_load_plugin_module_single_file(temp_plugins_dir: Path):
    """Test loading single-file plugin."""
    plugin_file = temp_plugins_dir / "simple_plugin.py"
    plugin_file.write_text("test_var = 'hello'")

    loader = PluginLoader()
    module = loader.load_plugin_module(plugin_file)

    assert hasattr(module, "test_var")
    assert module.test_var == "hello"


def test_load_plugin_module_directory(temp_plugins_dir: Path):
    """Test loading directory plugin."""
    plugin_dir = temp_plugins_dir / "dir_plugin"
    plugin_dir.mkdir()
    (plugin_dir / "__init__.py").write_text("plugin_name = 'test'")

    loader = PluginLoader()
    module = loader.load_plugin_module(plugin_dir)

    assert hasattr(module, "plugin_name")
    assert module.plugin_name == "test"


def test_parse_plugin_metadata_no_file(temp_plugins_dir: Path):
    """Test parsing metadata when no file exists."""
    plugin_file = temp_plugins_dir / "plugin.py"
    plugin_file.write_text("")

    loader = PluginLoader()
    metadata = loader.parse_plugin_metadata(plugin_file)

    assert metadata == {}


def test_parse_plugin_metadata_from_file(temp_plugins_dir: Path):
    """Test parsing metadata from plugin.yaml."""
    plugin_dir = temp_plugins_dir / "plugin"
    plugin_dir.mkdir()
    (plugin_dir / "__init__.py").write_text("")

    metadata_file = plugin_dir / "plugin.yaml"
    metadata_file.write_text("name: test\nversion: 1.0.0")

    loader = PluginLoader()
    metadata = loader.parse_plugin_metadata(plugin_dir)

    assert metadata == {"name": "test", "version": "1.0.0"}


def test_parse_plugin_metadata_handles_empty_yaml(temp_plugins_dir: Path):
    """Test parsing empty YAML file."""
    plugin_dir = temp_plugins_dir / "plugin"
    plugin_dir.mkdir()
    (plugin_dir / "plugin.yaml").write_text("")

    loader = PluginLoader()
    metadata = loader.parse_plugin_metadata(plugin_dir)

    assert metadata == {}


def test_parse_plugin_metadata_handles_invalid_yaml(temp_plugins_dir: Path):
    """Test parsing invalid YAML file."""
    plugin_dir = temp_plugins_dir / "plugin"
    plugin_dir.mkdir()
    (plugin_dir / "plugin.yaml").write_text("invalid: yaml: content:")

    loader = PluginLoader()
    metadata = loader.parse_plugin_metadata(plugin_dir)

    assert metadata == {}
