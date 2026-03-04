"""Plugin manager coordinating plugin system."""

import json
import logging
import sqlite3
import sys
from pathlib import Path
from typing import Any

import orjson
import pluggy

from smk.core.config.paths import get_data_dir
from smk.core.plugins.cache import PluginCache
from smk.core.plugins.dependencies import PluginDependencyManager
from smk.core.plugins.loader import PluginLoader

logger = logging.getLogger(__name__)


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
                logger.info("Plugin loaded: %s", plugin_name)
            except Exception as e:
                plugin_name = getattr(plugin_module, "__name__", "unknown")
                self.failed_plugins[plugin_name] = str(e)
                logger.warning("Plugin failed to load: %s — %s", plugin_name, e)

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
            logger.info("Plugin loaded: %s", plugin_name)

        except Exception as e:
            self.failed_plugins[plugin_name] = f"Failed to load: {e!s}"
            logger.warning("Plugin failed to load: %s — %s", plugin_name, e)

    def get_loaded_plugins(self) -> dict[str, Any]:
        """Get dictionary of successfully loaded plugins.

        Returns:
            Dictionary mapping plugin name to module.
        """
        return self.loaded_plugins.copy()

    def get_entity_types(self, source_plugin: str) -> list[dict]:
        """Return entity types for the active source plugin."""
        results = self.pm.hook.smk_get_entity_types(source_plugin=source_plugin)
        types = []
        for result in results:
            if result is not None:
                types.extend(result)
        return types

    def get_source_plugins(self) -> list[dict]:
        """Return metadata dicts for all registered source plugins."""
        return [r for r in self.pm.hook.smk_get_source_info() if r is not None]

    def run_audit(self, source_plugin: str, entity_types: list[dict]) -> dict[str, list[dict]]:
        """Run audit for each entity type. Returns {entity_type_id: [issues]}."""
        data_dir = get_data_dir(subdir="source")
        audit_results: dict[str, list[dict]] = {}
        for et in entity_types:
            entity_type_id = et["id"]
            path = data_dir / f"{entity_type_id}.json"
            if not path.exists():
                audit_results[entity_type_id] = []
                continue
            entities = orjson.loads(path.read_bytes())
            all_issues = self.pm.hook.smk_audit_entity_type(
                entity_type=entity_type_id,
                entities=entities,
                source_plugin=source_plugin,
            )
            issues = []
            for result in all_issues:
                if result is not None:
                    issues.extend(result)
            audit_results[entity_type_id] = issues
        return audit_results

    def get_failed_plugins(self) -> dict[str, str]:
        """Get dictionary of failed plugins with error messages.

        Returns:
            Dictionary mapping plugin name to error message.
        """
        return self.failed_plugins.copy()

    def transform_entity(self, entity_type: str, entity: dict[str, Any], source_plugin: str) -> dict[str, Any] | None:
        """Call smk_transform_entity; return first non-None result."""
        results = self.pm.hook.smk_transform_entity(
            entity_type=entity_type,
            entity=entity,
            source_plugin=source_plugin,
        )
        for result in results:
            if result is not None:
                return result
        return None

    def transform_batch(self, batch_id: int, source_plugin: str, db: sqlite3.Connection) -> None:
        """Transform all 'selected' entities in the batch.

        For each entity:
        1. Set status=transforming in DB
        2. Look up parent's hcl_resource_name from DB; inject as
           _smk_parent_hcl_resource_name into a copy of source_entity
        3. Call transform_entity()
        4. On success: update_entity_transform(spacelift_entity, hcl_resource_name)
        5. On exception: update_entity_error(str(e))
        """
        from smk.core.db.entities import get_batch_entities, update_entity_error, update_entity_transform

        selected = get_batch_entities(db, batch_id, status="selected")
        for ent in selected:
            entity_type = ent["entity_type"]
            entity_id = ent["entity_id"]

            # Mark as transforming
            db.execute(
                "UPDATE batch_entities SET status = 'transforming'"
                " WHERE batch_id = ? AND entity_type = ? AND entity_id = ?",
                (batch_id, entity_type, entity_id),
            )
            db.commit()

            try:
                source_entity: dict[str, Any] = json.loads(ent["source_entity"] or "{}")

                # Inject parent HCL resource name if available
                if ent.get("parent_type") and ent.get("parent_id"):
                    parent_row = db.execute(
                        """
                        SELECT hcl_resource_name FROM batch_entities
                        WHERE entity_type = ? AND entity_id = ?
                        """,
                        (ent["parent_type"], ent["parent_id"]),
                    ).fetchone()
                    if parent_row and parent_row["hcl_resource_name"]:
                        source_entity = {
                            **source_entity,
                            "_smk_parent_hcl_resource_name": parent_row["hcl_resource_name"],
                        }

                result = self.transform_entity(entity_type, source_entity, source_plugin)
                if result is None:
                    raise ValueError(f"No plugin handled entity_type={entity_type!r}")

                update_entity_transform(
                    db,
                    batch_id,
                    entity_type,
                    entity_id,
                    spacelift_entity=result,
                    hcl_resource_name=f"{result['resource_type']}.{result['resource_name']}",
                )
            except Exception as e:
                update_entity_error(db, batch_id, entity_type, entity_id, str(e))

    def is_development_mode(self) -> bool:
        """Check if running in development mode.

        Returns:
            True if in development mode (not bundled).
        """
        return not self.is_bundled
