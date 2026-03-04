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


def test_get_entity_types_flattens_results() -> None:
    """get_entity_types flattens lists and filters None."""
    manager = SMKPluginManager()

    with patch.object(
        manager.pm.hook,
        "smk_get_entity_types",
        return_value=[None, [{"id": "workspaces", "display_name": "Workspaces"}]],
    ):
        result = manager.get_entity_types("hashicorp")

    assert len(result) == 1
    assert result[0]["id"] == "workspaces"


def test_get_entity_types_returns_empty_when_all_none() -> None:
    """get_entity_types returns empty list when all plugins return None."""
    manager = SMKPluginManager()

    with patch.object(manager.pm.hook, "smk_get_entity_types", return_value=[None, None]):
        result = manager.get_entity_types("unknown")

    assert result == []


def test_run_audit_returns_empty_when_file_missing(tmp_path: Path) -> None:
    """run_audit returns empty issues list when entity file doesn't exist."""
    from unittest.mock import patch as upatch

    manager = SMKPluginManager()
    entity_types = [{"id": "workspaces", "display_name": "Workspaces"}]

    with upatch("smk.core.plugins.manager.get_data_dir", return_value=tmp_path):
        result = manager.run_audit("hashicorp", entity_types)

    assert result == {"workspaces": []}


def test_run_audit_calls_hook_and_aggregates(tmp_path: Path) -> None:
    """run_audit reads entities from disk, calls hook, and aggregates results."""
    from unittest.mock import patch as upatch

    import orjson

    manager = SMKPluginManager()
    entities = [{"id": "ws-1"}]
    (tmp_path / "workspaces.json").write_bytes(orjson.dumps(entities))

    issues = [{"entity_id": "ws-1", "severity": "warning", "message": "No VCS configuration"}]

    with (
        upatch("smk.core.plugins.manager.get_data_dir", return_value=tmp_path),
        patch.object(manager.pm.hook, "smk_audit_entity_type", return_value=[issues]),
    ):
        result = manager.run_audit("hashicorp", [{"id": "workspaces", "display_name": "Workspaces"}])

    assert result == {"workspaces": issues}


def test_run_audit_filters_none_from_hook(tmp_path: Path) -> None:
    """run_audit skips None results from hook calls."""
    from unittest.mock import patch as upatch

    import orjson

    manager = SMKPluginManager()
    (tmp_path / "workspaces.json").write_bytes(orjson.dumps([]))

    with (
        upatch("smk.core.plugins.manager.get_data_dir", return_value=tmp_path),
        patch.object(manager.pm.hook, "smk_audit_entity_type", return_value=[None]),
    ):
        result = manager.run_audit("hashicorp", [{"id": "workspaces", "display_name": "Workspaces"}])

    assert result == {"workspaces": []}


def test_transform_entity_returns_first_non_none() -> None:
    """transform_entity returns first non-None result from hook."""
    manager = SMKPluginManager()
    expected = {"resource_type": "spacelift_space", "resource_name": "org_x", "attributes": {}}

    with patch.object(manager.pm.hook, "smk_transform_entity", return_value=[None, expected]):
        result = manager.transform_entity("organizations", {"id": "org-1", "name": "x"}, "hashicorp")

    assert result == expected


def test_transform_entity_returns_none_when_all_none() -> None:
    """transform_entity returns None when all plugins return None."""
    manager = SMKPluginManager()

    with patch.object(manager.pm.hook, "smk_transform_entity", return_value=[None, None]):
        result = manager.transform_entity("organizations", {"id": "org-1"}, "hashicorp")

    assert result is None


def test_transform_batch_processes_selected_entities(tmp_path: Path) -> None:
    """transform_batch transforms all selected entities."""
    import json

    from smk.core.db import get_db
    from smk.core.db.batches import create_batch

    db = get_db(tmp_path)
    batch = create_batch(db)
    db.execute(
        """INSERT INTO batch_entities
           (batch_id, entity_type, entity_id, entity_name, status, source_entity)
           VALUES (?, 'organizations', 'org-1', 'my-org', 'selected', ?)""",
        (batch["id"], json.dumps({"id": "org-1", "name": "my-org"})),
    )
    db.commit()

    manager = SMKPluginManager()
    result = {
        "resource_type": "spacelift_space",
        "resource_name": "org_my_org",
        "attributes": {"name": "my-org", "parent_space_id": "root"},
    }

    with patch.object(manager, "transform_entity", return_value=result):
        manager.transform_batch(batch["id"], "hashicorp", db)

    row = db.execute("SELECT status, hcl_resource_name FROM batch_entities WHERE entity_id = 'org-1'").fetchone()
    assert row["status"] == "ready"
    assert row["hcl_resource_name"] == "spacelift_space.org_my_org"
    db.close()


def test_transform_batch_records_error_on_exception(tmp_path: Path) -> None:
    """transform_batch records error when transform_entity raises."""
    import json

    from smk.core.db import get_db
    from smk.core.db.batches import create_batch

    db = get_db(tmp_path)
    batch = create_batch(db)
    db.execute(
        """INSERT INTO batch_entities
           (batch_id, entity_type, entity_id, entity_name, status, source_entity)
           VALUES (?, 'workspaces', 'ws-1', 'prod', 'selected', ?)""",
        (batch["id"], json.dumps({"id": "ws-1", "name": "prod"})),
    )
    db.commit()

    manager = SMKPluginManager()

    with patch.object(manager, "transform_entity", side_effect=ValueError("boom")):
        manager.transform_batch(batch["id"], "hashicorp", db)

    row = db.execute("SELECT status, error_message FROM batch_entities WHERE entity_id = 'ws-1'").fetchone()
    assert row["status"] == "error"
    assert "boom" in row["error_message"]
    db.close()


def test_transform_batch_injects_parent_hcl_name(tmp_path: Path) -> None:
    """transform_batch injects _smk_parent_hcl_resource_name when parent is ready."""
    import json

    from smk.core.db import get_db
    from smk.core.db.batches import create_batch

    db = get_db(tmp_path)
    batch = create_batch(db)
    # Parent org is already ready
    db.execute(
        """INSERT INTO batch_entities
           (batch_id, entity_type, entity_id, entity_name, status, source_entity, hcl_resource_name)
           VALUES (?, 'organizations', 'org-1', 'my-org', 'ready', ?, 'spacelift_space.org_my_org')""",
        (batch["id"], json.dumps({"id": "org-1", "name": "my-org"})),
    )
    # Child project
    db.execute(
        """INSERT INTO batch_entities
           (batch_id, entity_type, entity_id, entity_name, parent_type, parent_id, status, source_entity)
           VALUES (?, 'projects', 'prj-1', 'default', 'organizations', 'org-1', 'selected', ?)""",
        (batch["id"], json.dumps({"id": "prj-1", "name": "default"})),
    )
    db.commit()

    captured_entities = []

    def capture_transform(_entity_type, entity, _source_plugin):
        captured_entities.append(entity)
        return {
            "resource_type": "spacelift_space",
            "resource_name": "proj_default",
            "attributes": {},
        }

    manager = SMKPluginManager()
    with patch.object(manager, "transform_entity", side_effect=capture_transform):
        manager.transform_batch(batch["id"], "hashicorp", db)

    assert any("_smk_parent_hcl_resource_name" in e for e in captured_entities)
    parent_injected = next(e for e in captured_entities if "_smk_parent_hcl_resource_name" in e)
    assert parent_injected["_smk_parent_hcl_resource_name"] == "spacelift_space.org_my_org"
    db.close()


def test_transform_batch_no_result_sets_error(tmp_path: Path) -> None:
    """transform_batch records error when transform_entity returns None."""
    import json

    from smk.core.db import get_db
    from smk.core.db.batches import create_batch

    db = get_db(tmp_path)
    batch = create_batch(db)
    db.execute(
        """INSERT INTO batch_entities
           (batch_id, entity_type, entity_id, entity_name, status, source_entity)
           VALUES (?, 'workspaces', 'ws-1', 'prod', 'selected', ?)""",
        (batch["id"], json.dumps({"id": "ws-1", "name": "prod"})),
    )
    db.commit()

    manager = SMKPluginManager()
    with patch.object(manager, "transform_entity", return_value=None):
        manager.transform_batch(batch["id"], "hashicorp", db)

    row = db.execute("SELECT status FROM batch_entities WHERE entity_id = 'ws-1'").fetchone()
    assert row["status"] == "error"
    db.close()


def test_transform_batch_no_parent_hcl_when_parent_not_in_batch(tmp_path: Path) -> None:
    """transform_batch does not inject parent name when parent is absent from batch."""
    import json

    from smk.core.db import get_db
    from smk.core.db.batches import create_batch

    db = get_db(tmp_path)
    batch = create_batch(db)
    # Child project with parent_type + parent_id set, but parent NOT in batch
    db.execute(
        """INSERT INTO batch_entities
           (batch_id, entity_type, entity_id, entity_name, parent_type, parent_id, status, source_entity)
           VALUES (?, 'projects', 'prj-1', 'default', 'organizations', 'org-99', 'selected', ?)""",
        (batch["id"], json.dumps({"id": "prj-1", "name": "default"})),
    )
    db.commit()

    captured_entities = []

    def capture_transform(_entity_type, entity, _source_plugin):
        captured_entities.append(entity)
        return {"resource_type": "spacelift_space", "resource_name": "x", "attributes": {}}

    manager = SMKPluginManager()
    with patch.object(manager, "transform_entity", side_effect=capture_transform):
        manager.transform_batch(batch["id"], "hashicorp", db)

    # prj-1 should NOT have _smk_parent_hcl_resource_name since org-99 is not in batch
    assert "_smk_parent_hcl_resource_name" not in captured_entities[0]
    db.close()
