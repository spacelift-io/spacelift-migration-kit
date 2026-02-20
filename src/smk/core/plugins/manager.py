"""Plugin manager coordinating plugin system."""

import sys
from pathlib import Path
from typing import Any

import pluggy

from smk.core.plugins.cache import PluginCache
from smk.core.plugins.dependencies import PluginDependencyManager
from smk.core.plugins.loader import PluginLoader


class SMKPluginManager:
    """Main plugin manager coordinating plugin system.

    Handles plugin discovery, loading, dependency management, and hook registration.
    Supports both development and bundled deployment modes.
    """

    def __init__(self) -> None:
        """Initialize plugin manager."""
        self.pm = pluggy.PluginManager("smk")
        self.cache = PluginCache()
        self.is_bundled = self._detect_bundled_mode()
        self.dep_manager = PluginDependencyManager(self.cache, self.is_bundled)
        self.loader = PluginLoader()

        # Register hook specifications
        from smk.core.plugins import hooks as hook_specs

        self.pm.add_hookspecs(hook_specs)

        # Track loaded plugins
        self.loaded_plugins: dict[str, Any] = {}
        self.failed_plugins: dict[str, str] = {}

    def _detect_bundled_mode(self) -> bool:
        """Detect if running from PyInstaller bundle.

        Returns:
            True if running from bundle, False otherwise.
        """
        return getattr(sys, "frozen", False)

    def initialize(self) -> None:
        """Initialize plugin system by loading all plugins."""
        # Load built-in plugins
        self._load_builtin_plugins()

        # Load third-party plugins
        self._load_third_party_plugins()

    def _load_builtin_plugins(self) -> None:
        """Load built-in plugins from src/smk/plugins/."""
        builtin_plugins = self.loader.discover_builtin_plugins()

        for plugin_module in builtin_plugins:
            try:
                self.pm.register(plugin_module)
                plugin_name = getattr(plugin_module, "__name__", "unknown")
                self.loaded_plugins[plugin_name] = plugin_module
            except Exception as e:
                plugin_name = getattr(plugin_module, "__name__", "unknown")
                self.failed_plugins[plugin_name] = str(e)

    def _load_third_party_plugins(self) -> None:
        """Load third-party plugins from ~/.config/smk/plugins/."""
        plugin_paths = self.loader.discover_third_party_plugins()

        for plugin_path in plugin_paths:
            self._load_plugin(plugin_path)

    def _load_plugin(self, plugin_path: Path) -> None:
        """Load single plugin from path.

        Args:
            plugin_path: Path to plugin file or directory.
        """
        plugin_name = plugin_path.stem if plugin_path.is_file() else plugin_path.name

        try:
            # Check and handle dependencies
            success, error = self.dep_manager.handle_dependencies(plugin_path)
            if not success:
                self.failed_plugins[plugin_name] = error or "Dependency check failed"
                return

            # Load plugin module
            module = self.loader.load_plugin_module(plugin_path)

            # Register with pluggy
            self.pm.register(module)

            # Track successful load
            self.loaded_plugins[plugin_name] = module

        except Exception as e:
            self.failed_plugins[plugin_name] = f"Failed to load: {e!s}"

    def get_loaded_plugins(self) -> dict[str, Any]:
        """Get dictionary of successfully loaded plugins.

        Returns:
            Dictionary mapping plugin name to module.
        """
        return self.loaded_plugins.copy()

    def get_source_plugins(self) -> list[dict]:
        """Return metadata dicts for all registered source plugins."""
        return [r for r in self.pm.hook.smk_get_source_info() if r is not None]

    def get_failed_plugins(self) -> dict[str, str]:
        """Get dictionary of failed plugins with error messages.

        Returns:
            Dictionary mapping plugin name to error message.
        """
        return self.failed_plugins.copy()

    def is_development_mode(self) -> bool:
        """Check if running in development mode.

        Returns:
            True if in development mode (not bundled).
        """
        return not self.is_bundled
