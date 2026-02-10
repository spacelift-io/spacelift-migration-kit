"""Plugin discovery and loading logic."""

import importlib.util
import sys
from pathlib import Path
from typing import Any

from smk.core.config.paths import get_plugins_dir


class PluginLoader:
    """Discovers and loads plugins from filesystem."""

    def __init__(self) -> None:
        """Initialize plugin loader."""
        self.plugins_dir = get_plugins_dir()

    def discover_builtin_plugins(self) -> list[Any]:
        """Discover built-in plugins from src/smk/plugins/.

        Returns:
            List of built-in plugin modules.
        """
        # Built-in plugins are explicitly imported, not discovered
        # This list will be populated as built-in plugins are added
        builtin_plugins = []

        # Example of how to import built-in plugins when they exist:
        # try:
        #     from smk.plugins import terraform_cloud
        #     builtin_plugins.append(terraform_cloud)
        # except ImportError:
        #     pass

        return builtin_plugins

    def discover_third_party_plugins(self) -> list[Path]:
        """Discover third-party plugins from ~/.config/smk/plugins/.

        Returns:
            List of plugin paths (directories or .py files).
        """
        if not self.plugins_dir.exists():
            return []

        plugins = []

        # Find all .py files and directories with __init__.py
        for item in self.plugins_dir.iterdir():
            is_py_file = item.is_file() and item.suffix == ".py" and item.stem != "__init__"
            is_plugin_dir = item.is_dir() and (item / "__init__.py").exists()
            if is_py_file or is_plugin_dir:
                plugins.append(item)

        return sorted(plugins)

    def load_plugin_module(self, plugin_path: Path) -> Any:
        """Load plugin module from path.

        Args:
            plugin_path: Path to plugin file or directory.

        Returns:
            Loaded module object.

        Raises:
            ImportError: If plugin cannot be loaded.
        """
        if plugin_path.is_file():
            # Single-file plugin
            module_name = f"smk_plugin_{plugin_path.stem}"
            spec = importlib.util.spec_from_file_location(module_name, plugin_path)
        else:
            # Package plugin
            module_name = f"smk_plugin_{plugin_path.name}"
            init_file = plugin_path / "__init__.py"
            spec = importlib.util.spec_from_file_location(module_name, init_file)

        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot load plugin from {plugin_path}")

        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)

        return module

    def parse_plugin_metadata(self, plugin_path: Path) -> dict[str, Any]:
        """Parse plugin.yaml metadata if present.

        Args:
            plugin_path: Path to plugin directory or file.

        Returns:
            Metadata dictionary.
        """
        import yaml

        # Determine metadata file location
        metadata_file = plugin_path.parent / "plugin.yaml" if plugin_path.is_file() else plugin_path / "plugin.yaml"

        if not metadata_file.exists():
            return {}

        try:
            with metadata_file.open("r") as f:
                return yaml.safe_load(f) or {}
        except Exception:
            return {}
