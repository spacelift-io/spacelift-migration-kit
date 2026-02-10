"""Tests for plugin dependency manager."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from smk.core.plugins.cache import PluginCache
from smk.core.plugins.dependencies import PluginDependencyManager


@pytest.fixture
def temp_deps_dir(tmp_path: Path) -> Path:
    """Create temporary deps directory."""
    return tmp_path / "plugin-deps"


@pytest.fixture
def mock_cache() -> PluginCache:
    """Create mock cache."""
    cache = MagicMock(spec=PluginCache)
    cache.is_dependencies_installed.return_value = False
    return cache


@pytest.fixture
def dep_manager_dev(mock_cache: PluginCache, temp_deps_dir: Path) -> PluginDependencyManager:
    """Create dependency manager in development mode."""
    manager = PluginDependencyManager(mock_cache, is_bundled=False)
    manager.deps_dir = temp_deps_dir
    return manager


@pytest.fixture
def dep_manager_bundled(mock_cache: PluginCache, temp_deps_dir: Path) -> PluginDependencyManager:
    """Create dependency manager in bundled mode."""
    manager = PluginDependencyManager(mock_cache, is_bundled=True)
    manager.deps_dir = temp_deps_dir
    return manager


def test_init_sets_bundled_mode():
    """Test initialization sets bundled mode."""
    cache = MagicMock()
    manager = PluginDependencyManager(cache, is_bundled=True)
    assert manager.is_bundled is True


def test_check_dependencies_no_requirements_file(dep_manager_dev: PluginDependencyManager, tmp_path: Path):
    """Test checking dependencies when no requirements.txt exists."""
    plugin_path = tmp_path / "plugin.py"
    plugin_path.write_text("")

    has_deps, missing = dep_manager_dev.check_dependencies(plugin_path)

    assert has_deps is False
    assert missing == []


def test_check_dependencies_returns_cached(tmp_path: Path, mock_cache: PluginCache, temp_deps_dir: Path):
    """Test checking dependencies uses cache."""
    plugin_path = tmp_path / "plugin"
    plugin_path.mkdir()
    (plugin_path / "requirements.txt").write_text("boto3")

    # Configure mock to return True for this test
    mock_cache.is_dependencies_installed.return_value = True  # type: ignore[attr-defined]

    dep_manager = PluginDependencyManager(mock_cache, is_bundled=False)
    dep_manager.deps_dir = temp_deps_dir

    has_deps, missing = dep_manager.check_dependencies(plugin_path)

    assert has_deps is True
    assert missing == []


def test_check_dependencies_with_requirements(dep_manager_dev: PluginDependencyManager, tmp_path: Path):
    """Test checking dependencies with requirements file."""
    plugin_path = tmp_path / "plugin"
    plugin_path.mkdir()
    (plugin_path / "requirements.txt").write_text("nonexistent-package-xyz")

    has_deps, missing = dep_manager_dev.check_dependencies(plugin_path)

    assert has_deps is True
    assert "nonexistent-package-xyz" in missing


def test_handle_dependencies_no_requirements(dep_manager_dev: PluginDependencyManager, tmp_path: Path):
    """Test handling dependencies with no requirements."""
    plugin_path = tmp_path / "plugin.py"
    plugin_path.write_text("")

    success, error = dep_manager_dev.handle_dependencies(plugin_path)

    assert success is True
    assert error is None


def test_handle_dependencies_dev_mode_missing(dep_manager_dev: PluginDependencyManager, tmp_path: Path):
    """Test handling missing dependencies in development mode."""
    plugin_path = tmp_path / "plugin"
    plugin_path.mkdir()
    (plugin_path / "requirements.txt").write_text("nonexistent-pkg")

    success, error = dep_manager_dev.handle_dependencies(plugin_path)

    assert success is False
    assert error is not None
    assert "nonexistent-pkg" in error
    assert "uv add" in error


def test_extract_package_name_simple():
    """Test extracting package name from simple requirement."""
    cache = MagicMock()
    manager = PluginDependencyManager(cache, False)

    name = manager._extract_package_name("boto3")
    assert name == "boto3"


def test_extract_package_name_with_version():
    """Test extracting package name with version specifier."""
    cache = MagicMock()
    manager = PluginDependencyManager(cache, False)

    assert manager._extract_package_name("boto3>=1.26.0") == "boto3"
    assert manager._extract_package_name("requests==2.28.0") == "requests"
    assert manager._extract_package_name("package<=1.0") == "package"


def test_is_package_available_builtin(dep_manager_dev: PluginDependencyManager):
    """Test checking if builtin package is available."""
    result = dep_manager_dev._is_package_available("sys")
    assert result is True


def test_is_package_available_installed(dep_manager_dev: PluginDependencyManager):
    """Test checking if installed package is available."""
    result = dep_manager_dev._is_package_available("pytest")
    assert result is True


def test_is_package_available_missing(dep_manager_dev: PluginDependencyManager):
    """Test checking if missing package is unavailable."""
    result = dep_manager_dev._is_package_available("nonexistent-package-xyz")
    assert result is False


def test_get_requirements_from_file(dep_manager_dev: PluginDependencyManager, tmp_path: Path):
    """Test getting requirements from file."""
    plugin_path = tmp_path / "plugin"
    plugin_path.mkdir()
    req_file = plugin_path / "requirements.txt"
    req_file.write_text("boto3>=1.26.0\nrequests\n# comment\n\npyyaml")

    requirements = dep_manager_dev._get_requirements(plugin_path)

    assert "boto3>=1.26.0" in requirements
    assert "requests" in requirements
    assert "pyyaml" in requirements
    assert len(requirements) == 3


def test_get_requirements_single_file_plugin(dep_manager_dev: PluginDependencyManager, tmp_path: Path):
    """Test getting requirements for single-file plugin."""
    plugin_file = tmp_path / "plugin.py"
    plugin_file.write_text("")
    req_file = tmp_path / "requirements.txt"
    req_file.write_text("boto3")

    requirements = dep_manager_dev._get_requirements(plugin_file)

    assert requirements == ["boto3"]
