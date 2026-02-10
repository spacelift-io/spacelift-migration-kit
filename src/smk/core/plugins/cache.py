"""Plugin cache management for tracking installation state."""

import json
from pathlib import Path
from typing import Any

from smk.core.config.paths import get_plugin_cache_file


class PluginCache:
    """Manages plugin installation cache.

    Tracks which plugins have been loaded and which dependencies have been installed.
    Prevents redundant dependency checks and installations across app restarts.
    """

    def __init__(self, cache_file: Path | None = None) -> None:
        """Initialize plugin cache.

        Args:
            cache_file: Path to cache file. Uses default if None.
        """
        self.cache_file = cache_file or get_plugin_cache_file()
        self._cache: dict[str, Any] = self._load_cache()

    def _load_cache(self) -> dict[str, Any]:
        """Load cache from disk.

        Returns:
            Cache dictionary.
        """
        if not self.cache_file.exists():
            return {}

        try:
            with self.cache_file.open("r") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return {}

    def _save_cache(self) -> None:
        """Save cache to disk."""
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        with self.cache_file.open("w") as f:
            json.dump(self._cache, f, indent=2)

    def get_plugin_hash(self, plugin_path: Path) -> str | None:
        """Get cached hash for plugin.

        Args:
            plugin_path: Path to plugin.

        Returns:
            Hash string if cached, None otherwise.
        """
        plugin_key = str(plugin_path)
        return self._cache.get(plugin_key, {}).get("hash")

    def is_dependencies_installed(self, plugin_path: Path) -> bool:
        """Check if plugin dependencies are installed.

        Args:
            plugin_path: Path to plugin.

        Returns:
            True if dependencies are installed and cached.
        """
        plugin_key = str(plugin_path)
        return self._cache.get(plugin_key, {}).get("dependencies_installed", False)

    def set_dependencies_installed(self, plugin_path: Path, installed: bool = True) -> None:
        """Mark plugin dependencies as installed.

        Args:
            plugin_path: Path to plugin.
            installed: Installation state.
        """
        plugin_key = str(plugin_path)
        if plugin_key not in self._cache:
            self._cache[plugin_key] = {}
        self._cache[plugin_key]["dependencies_installed"] = installed
        self._save_cache()

    def set_plugin_hash(self, plugin_path: Path, file_hash: str) -> None:
        """Set hash for plugin.

        Args:
            plugin_path: Path to plugin.
            file_hash: Hash of plugin file(s).
        """
        plugin_key = str(plugin_path)
        if plugin_key not in self._cache:
            self._cache[plugin_key] = {}
        self._cache[plugin_key]["hash"] = file_hash
        self._save_cache()
