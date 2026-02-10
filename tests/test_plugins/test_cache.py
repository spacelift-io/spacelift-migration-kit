"""Tests for plugin cache."""

import json
from pathlib import Path

import pytest

from smk.core.plugins.cache import PluginCache


@pytest.fixture
def temp_cache_file(tmp_path: Path) -> Path:
    """Create temporary cache file."""
    return tmp_path / "plugin-cache.json"


def test_plugin_cache_init_creates_empty_cache(temp_cache_file: Path) -> None:
    """Test cache initialization with no existing file."""
    cache = PluginCache(temp_cache_file)
    assert cache._cache == {}


def test_plugin_cache_loads_existing_cache(temp_cache_file: Path) -> None:
    """Test cache loads from existing file."""
    # Create existing cache file
    cache_data = {"plugin1": {"hash": "abc123"}}
    temp_cache_file.write_text(json.dumps(cache_data))

    cache = PluginCache(temp_cache_file)
    assert cache._cache == cache_data


def test_get_plugin_hash_returns_none_for_new_plugin(temp_cache_file: Path) -> None:
    """Test getting hash for plugin not in cache."""
    cache = PluginCache(temp_cache_file)
    result = cache.get_plugin_hash(Path("/fake/plugin"))
    assert result is None


def test_set_and_get_plugin_hash(temp_cache_file: Path) -> None:
    """Test setting and getting plugin hash."""
    cache = PluginCache(temp_cache_file)
    plugin_path = Path("/fake/plugin")

    cache.set_plugin_hash(plugin_path, "abc123")
    result = cache.get_plugin_hash(plugin_path)

    assert result == "abc123"


def test_is_dependencies_installed_defaults_false(temp_cache_file: Path) -> None:
    """Test dependencies installed check for new plugin."""
    cache = PluginCache(temp_cache_file)
    result = cache.is_dependencies_installed(Path("/fake/plugin"))
    assert result is False


def test_set_dependencies_installed(temp_cache_file: Path) -> None:
    """Test marking dependencies as installed."""
    cache = PluginCache(temp_cache_file)
    plugin_path = Path("/fake/plugin")

    cache.set_dependencies_installed(plugin_path, True)
    result = cache.is_dependencies_installed(plugin_path)

    assert result is True


def test_cache_persists_to_disk(temp_cache_file: Path) -> None:
    """Test cache saves to disk."""
    cache = PluginCache(temp_cache_file)
    plugin_path = Path("/fake/plugin")

    cache.set_plugin_hash(plugin_path, "xyz789")

    # Load new cache instance from same file
    cache2 = PluginCache(temp_cache_file)
    assert cache2.get_plugin_hash(plugin_path) == "xyz789"


def test_cache_handles_corrupted_file(temp_cache_file: Path) -> None:
    """Test cache handles corrupted JSON file."""
    temp_cache_file.write_text("not valid json{")

    cache = PluginCache(temp_cache_file)
    assert cache._cache == {}
