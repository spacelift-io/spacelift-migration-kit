"""Tests for entity CRUD, pagination, and auto-dependency resolution."""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from smk.core.db.batches import create_batch
from smk.core.db.connection import get_db
from smk.core.db.entities import (
    deselect_entities,
    get_batch_entities,
    list_entities,
    select_entities,
    update_entity_error,
    update_entity_transform,
)

_SQL_WS = (
    "INSERT INTO batch_entities"
    " (batch_id, entity_type, entity_id, entity_name, status)"
    " VALUES (?, 'workspaces', ?, ?, ?)"
)

_SQL_PROJ = (
    "INSERT INTO batch_entities"
    " (batch_id, entity_type, entity_id, entity_name, auto_included, status)"
    " VALUES (?, 'projects', ?, ?, ?, ?)"
)


def _ins_ws(db, batch_id, eid, name, status):
    db.execute(_SQL_WS, (batch_id, eid, name, status))
    db.commit()


def _ins_proj(db, batch_id, eid, name, auto, status):
    db.execute(_SQL_PROJ, (batch_id, eid, name, auto, status))
    db.commit()


@pytest.fixture
def db(tmp_path: Path):
    conn = get_db(tmp_path)
    yield conn
    conn.close()


@pytest.fixture
def source_data(tmp_path: Path) -> Path:
    """Write fake source data files."""
    source_dir = tmp_path / "data" / "source"
    source_dir.mkdir(parents=True)

    orgs = [{"id": "org-1", "name": "my-org"}]
    projects = [
        {"id": "prj-1", "name": "default", "organization": "org-1"},
        {"id": "prj-2", "name": "staging", "organization": "org-1"},
    ]
    workspaces = [
        {"id": "ws-1", "name": "prod-api", "project_id": "prj-1", "organization": "org-1"},
        {"id": "ws-2", "name": "staging-db", "project_id": "prj-2", "organization": "org-1"},
        {"id": "ws-3", "name": "legacy", "organization": "org-1"},
    ]

    (source_dir / "organizations.json").write_text(json.dumps(orgs))
    (source_dir / "projects.json").write_text(json.dumps(projects))
    (source_dir / "workspaces.json").write_text(json.dumps(workspaces))
    return source_dir


def _patch_source(source_dir: Path):
    """Patch _get_source_dir to return the test source_dir."""
    from smk.core.db import entities as ent_mod

    return patch.object(ent_mod, "_get_source_dir", return_value=source_dir)


def test_list_entities_no_source_returns_empty(db, tmp_path: Path) -> None:
    """list_entities returns empty when no source files."""
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()
    with patch("smk.core.db.entities._get_source_dir", return_value=empty_dir):
        result = list_entities(db, "workspaces")
    assert result["items"] == []
    assert result["total"] == 0


def test_list_entities_returns_all(db, source_data: Path) -> None:
    """list_entities returns all entities when no filter."""
    with _patch_source(source_data):
        result = list_entities(db, "workspaces")
    assert result["total"] == 3
    assert len(result["items"]) == 3


def test_list_entities_search_filters(db, source_data: Path) -> None:
    """list_entities filters by search string."""
    with _patch_source(source_data):
        result = list_entities(db, "workspaces", search="prod")
    assert result["total"] == 1
    assert result["items"][0]["entity_name"] == "prod-api"


def test_list_entities_pagination(db, source_data: Path) -> None:
    """list_entities returns correct page slice."""
    with _patch_source(source_data):
        result = list_entities(db, "workspaces", page=1, per_page=2)
    assert len(result["items"]) == 2
    assert result["total"] == 3


def test_list_entities_page_2(db, source_data: Path) -> None:
    """Page 2 returns remaining items."""
    with _patch_source(source_data):
        result = list_entities(db, "workspaces", page=2, per_page=2)
    assert len(result["items"]) == 1


def test_list_entities_batch_status_null_when_not_selected(db, source_data: Path) -> None:
    """batch_status is None for unselected entities."""
    with _patch_source(source_data):
        result = list_entities(db, "workspaces")
    assert all(item["batch_status"] is None for item in result["items"])


def test_list_entities_batch_status_selected(db, source_data: Path) -> None:
    """batch_status reflects selected status."""
    batch = create_batch(db)
    _ins_ws(db, batch["id"], "ws-1", "prod-api", "selected")
    with _patch_source(source_data):
        result = list_entities(db, "workspaces")
    statuses = {item["entity_id"]: item["batch_status"] for item in result["items"]}
    assert statuses["ws-1"] == "selected"
    assert statuses["ws-2"] is None


def test_list_entities_batch_status_migrated(db, source_data: Path) -> None:
    """batch_status is 'migrated' for entities in confirmed batches."""
    batch = create_batch(db)
    _ins_ws(db, batch["id"], "ws-1", "prod-api", "ready")
    db.execute("UPDATE batches SET status = 'confirmed' WHERE id = ?", (batch["id"],))
    db.commit()
    with _patch_source(source_data):
        result = list_entities(db, "workspaces")
    statuses = {item["entity_id"]: item["batch_status"] for item in result["items"]}
    assert statuses["ws-1"] == "migrated"


def test_list_entities_filter_selected(db, source_data: Path) -> None:
    """filter=selected returns only selected entities."""
    batch = create_batch(db)
    _ins_ws(db, batch["id"], "ws-1", "prod-api", "selected")
    with _patch_source(source_data):
        result = list_entities(db, "workspaces", filter_="selected")
    assert result["total"] == 1


def test_list_entities_filter_unselected(db, source_data: Path) -> None:
    """filter=unselected returns only entities not in any batch."""
    batch = create_batch(db)
    _ins_ws(db, batch["id"], "ws-1", "prod-api", "selected")
    with _patch_source(source_data):
        result = list_entities(db, "workspaces", filter_="unselected")
    assert result["total"] == 2
    ids = [i["entity_id"] for i in result["items"]]
    assert "ws-1" not in ids


def test_list_entities_filter_migrated(db, source_data: Path) -> None:
    """filter=migrated returns only confirmed entities."""
    batch = create_batch(db)
    _ins_ws(db, batch["id"], "ws-1", "prod-api", "ready")
    db.execute("UPDATE batches SET status = 'confirmed' WHERE id = ?", (batch["id"],))
    db.commit()
    with _patch_source(source_data):
        result = list_entities(db, "workspaces", filter_="migrated")
    assert result["total"] == 1
    assert result["items"][0]["entity_id"] == "ws-1"


def test_list_entities_filter_unmigrated(db, source_data: Path) -> None:
    """filter=unmigrated excludes confirmed entities."""
    batch = create_batch(db)
    _ins_ws(db, batch["id"], "ws-1", "prod-api", "ready")
    db.execute("UPDATE batches SET status = 'confirmed' WHERE id = ?", (batch["id"],))
    db.commit()
    with _patch_source(source_data):
        result = list_entities(db, "workspaces", filter_="unmigrated")
    assert all(item["entity_id"] != "ws-1" for item in result["items"])


def test_select_entities_adds_to_batch(db, source_data: Path) -> None:
    """select_entities adds entities to batch."""
    batch = create_batch(db)
    source_entities = [{"id": "ws-1", "name": "prod-api", "project_id": "prj-1", "organization": "org-1"}]
    with _patch_source(source_data):
        result = select_entities(db, batch["id"], "workspaces", ["ws-1"], source_entities)
    assert result["added"] >= 1


def test_select_entities_auto_includes_project(db, source_data: Path) -> None:
    """Selecting a workspace auto-includes its project."""
    batch = create_batch(db)
    source_entities = [{"id": "ws-1", "name": "prod-api", "project_id": "prj-1", "organization": "org-1"}]
    with _patch_source(source_data):
        result = select_entities(db, batch["id"], "workspaces", ["ws-1"], source_entities)
    # prj-1 should have been auto-included
    assert result["auto_added"] >= 1
    entities = get_batch_entities(db, batch["id"])
    entity_ids = {e["entity_id"] for e in entities}
    assert "prj-1" in entity_ids


def test_select_entities_auto_includes_org(db, source_data: Path) -> None:
    """Selecting a workspace auto-includes org if project's org not in batch."""
    batch = create_batch(db)
    source_entities = [{"id": "ws-1", "name": "prod-api", "project_id": "prj-1", "organization": "org-1"}]
    with _patch_source(source_data):
        select_entities(db, batch["id"], "workspaces", ["ws-1"], source_entities)
    entities = get_batch_entities(db, batch["id"])
    entity_ids = {e["entity_id"] for e in entities}
    assert "org-1" in entity_ids


def test_select_entities_already_migrated(db, source_data: Path) -> None:
    """select_entities skips already-migrated entities."""
    batch1 = create_batch(db)
    _ins_ws(db, batch1["id"], "ws-1", "prod-api", "ready")
    db.execute("UPDATE batches SET status = 'confirmed' WHERE id = ?", (batch1["id"],))
    db.commit()
    batch2 = create_batch(db)
    with _patch_source(source_data):
        result = select_entities(db, batch2["id"], "workspaces", ["ws-1"], [])
    assert result["already_migrated"] == 1
    assert result["added"] == 0


def test_select_entities_no_duplicate(db, source_data: Path) -> None:
    """Selecting same entity twice does not duplicate."""
    batch = create_batch(db)
    source_entities = [{"id": "ws-3", "name": "legacy", "organization": "org-1"}]
    with _patch_source(source_data):
        select_entities(db, batch["id"], "workspaces", ["ws-3"], source_entities)
        result = select_entities(db, batch["id"], "workspaces", ["ws-3"], source_entities)
    assert result["added"] == 0


def test_deselect_entities_removes(db) -> None:
    """deselect_entities removes entities from batch."""
    batch = create_batch(db)
    _ins_ws(db, batch["id"], "ws-1", "prod-api", "selected")
    removed = deselect_entities(db, batch["id"], "workspaces", ["ws-1"])
    assert removed == 1
    entities = get_batch_entities(db, batch["id"])
    assert not any(e["entity_id"] == "ws-1" for e in entities)


def test_deselect_nonexistent_returns_zero(db) -> None:
    """deselect_entities returns 0 for unknown entities."""
    batch = create_batch(db)
    removed = deselect_entities(db, batch["id"], "workspaces", ["ws-999"])
    assert removed == 0


def test_get_batch_entities_returns_list(db) -> None:
    """get_batch_entities returns list of entity dicts."""
    batch = create_batch(db)
    _ins_ws(db, batch["id"], "ws-1", "x", "selected")
    entities = get_batch_entities(db, batch["id"])
    assert len(entities) == 1
    assert entities[0]["entity_id"] == "ws-1"


def test_get_batch_entities_filter_by_status(db) -> None:
    """get_batch_entities filters by status."""
    batch = create_batch(db)
    _ins_ws(db, batch["id"], "ws-1", "x", "selected")
    _ins_ws(db, batch["id"], "ws-2", "y", "ready")
    ready = get_batch_entities(db, batch["id"], status="ready")
    assert len(ready) == 1
    assert ready[0]["entity_id"] == "ws-2"


def test_update_entity_transform(db) -> None:
    """update_entity_transform sets status to ready."""
    batch = create_batch(db)
    _ins_ws(db, batch["id"], "ws-1", "x", "transforming")
    update_entity_transform(
        db,
        batch["id"],
        "workspaces",
        "ws-1",
        spacelift_entity={
            "resource_type": "spacelift_stack",
            "resource_name": "ws_x",
            "attributes": {},
        },
        hcl_resource_name="spacelift_stack.ws_x",
    )
    row = db.execute("SELECT * FROM batch_entities WHERE entity_id = 'ws-1'").fetchone()
    assert row["status"] == "ready"
    assert row["hcl_resource_name"] == "spacelift_stack.ws_x"


def test_update_entity_error(db) -> None:
    """update_entity_error sets status to error."""
    batch = create_batch(db)
    _ins_ws(db, batch["id"], "ws-1", "x", "transforming")
    update_entity_error(db, batch["id"], "workspaces", "ws-1", "something went wrong")
    row = db.execute("SELECT * FROM batch_entities WHERE entity_id = 'ws-1'").fetchone()
    assert row["status"] == "error"
    assert row["error_message"] == "something went wrong"


def test_list_entities_org_has_no_parent(db, source_data: Path) -> None:
    """Organizations have no parent in list_entities."""
    with _patch_source(source_data):
        result = list_entities(db, "organizations")
    assert result["total"] == 1
    assert result["items"][0]["parent_id"] is None


def test_list_entities_auto_included_flag(db, source_data: Path) -> None:
    """auto_included=True is reflected in list_entities."""
    batch = create_batch(db)
    _ins_proj(db, batch["id"], "prj-1", "default", 1, "selected")
    with _patch_source(source_data):
        result = list_entities(db, "projects")
    item = next(i for i in result["items"] if i["entity_id"] == "prj-1")
    assert item["auto_included"] is True


def test_select_entities_workspace_without_project_uses_org(db, source_data: Path) -> None:
    """Workspace with no project_id auto-includes org as parent."""
    batch = create_batch(db)
    # ws-3 has no project_id, only organization
    source_entities = [{"id": "ws-3", "name": "legacy", "organization": "org-1"}]
    with _patch_source(source_data):
        select_entities(db, batch["id"], "workspaces", ["ws-3"], source_entities)
    entities = get_batch_entities(db, batch["id"])
    entity_ids = {e["entity_id"] for e in entities}
    # org-1 should be auto-included since project_id is absent
    assert "org-1" in entity_ids


def test_select_entities_organization_no_parent(db, source_data: Path) -> None:
    """Selecting an organization (no parent) increments added, not auto_added."""
    batch = create_batch(db)
    source_entities = [{"id": "org-1", "name": "my-org"}]
    with _patch_source(source_data):
        result = select_entities(db, batch["id"], "organizations", ["org-1"], source_entities)
    assert result["added"] == 1
    assert result["auto_added"] == 0


def test_select_entities_project_no_grandparent(db, source_data: Path) -> None:
    """Selecting a project auto-includes its org but has no grandparent."""
    batch = create_batch(db)
    source_entities = [{"id": "prj-1", "name": "default", "organization": "org-1"}]
    with _patch_source(source_data):
        result = select_entities(db, batch["id"], "projects", ["prj-1"], source_entities)
    assert result["added"] == 1
    # org-1 auto-included; no grandparent for orgs
    assert result["auto_added"] == 1


def test_extract_parent_type_workspace_with_project_id() -> None:
    """_extract_parent_type returns 'projects' when project_id present."""
    from smk.core.db.entities import _extract_parent_type

    entity = {"id": "ws-1", "project_id": "prj-1", "organization": "org-1"}
    assert _extract_parent_type(entity, "workspaces") == "projects"


def test_extract_parent_type_workspace_org_only() -> None:
    """_extract_parent_type returns 'organizations' when only organization set."""
    from smk.core.db.entities import _extract_parent_type

    entity = {"id": "ws-1", "project_id": None, "organization": "org-1"}
    assert _extract_parent_type(entity, "workspaces") == "organizations"


def test_extract_parent_type_workspace_json_api_project_rel() -> None:
    """_extract_parent_type returns 'projects' for JSON API project relationship."""
    from smk.core.db.entities import _extract_parent_type

    entity = {"relationships": {"project": {"data": {"id": "prj-99"}}}}
    assert _extract_parent_type(entity, "workspaces") == "projects"


def test_extract_parent_type_workspace_attributes_project_id() -> None:
    """_extract_parent_type returns 'projects' for attributes.project-id."""
    from smk.core.db.entities import _extract_parent_type

    entity = {"attributes": {"project-id": "prj-99"}}
    assert _extract_parent_type(entity, "workspaces") == "projects"


def test_extract_parent_type_workspace_no_parent() -> None:
    """_extract_parent_type falls back to 'projects' when no parent info."""
    from smk.core.db.entities import _extract_parent_type

    entity = {"id": "ws-1"}
    assert _extract_parent_type(entity, "workspaces") == "projects"


def test_extract_parent_type_project() -> None:
    """_extract_parent_type returns 'organizations' for projects."""
    from smk.core.db.entities import _extract_parent_type

    assert _extract_parent_type({}, "projects") == "organizations"


def test_extract_parent_id_project_json_api() -> None:
    """_extract_parent_id reads JSON API relationships.organization.data.id for projects."""
    from smk.core.db.entities import _extract_parent_id

    entity = {"relationships": {"organization": {"data": {"id": "org-99"}}}}
    assert _extract_parent_id(entity, "projects") == "org-99"


def test_select_entities_workspace_grandparent_missing(db, source_data: Path) -> None:
    """Workspace with project_id but project has no org does not crash."""
    import json as _json

    # Override source_data so projects.json has a project with no organization
    source_dir = source_data.parent / "source2"
    source_dir.mkdir()
    (source_dir / "organizations.json").write_text(_json.dumps([{"id": "org-1", "name": "my-org"}]))
    (source_dir / "projects.json").write_text(
        _json.dumps([{"id": "prj-x", "name": "no-org-project"}])  # no organization field
    )
    (source_dir / "workspaces.json").write_text(_json.dumps([{"id": "ws-x", "name": "ws", "project_id": "prj-x"}]))

    def _patch_source2(source_dir2):
        from smk.core.db import entities as ent_mod

        return patch.object(ent_mod, "_get_source_dir", return_value=source_dir2)

    batch = create_batch(db)
    source_entities = [{"id": "ws-x", "name": "ws", "project_id": "prj-x"}]
    with _patch_source2(source_dir):
        result = select_entities(db, batch["id"], "workspaces", ["ws-x"], source_entities)
    # prj-x auto-included; no grandparent since project has no org
    assert result["auto_added"] >= 1


def test_load_source_entity_not_found(tmp_path: Path) -> None:
    """_load_source_entity returns None when entity_id not in file."""
    import json as _json

    from smk.core.db.entities import _load_source_entity

    (tmp_path / "workspaces.json").write_text(_json.dumps([{"id": "ws-other"}]))
    with patch("smk.core.db.entities._get_source_dir", return_value=tmp_path):
        result = _load_source_entity("workspaces", "ws-missing")
    assert result is None


def test_select_entities_workspace_org_only_auto_includes_org(db, source_data: Path) -> None:
    """Workspace with no project_id auto-includes org (not a fake project)."""
    batch = create_batch(db)
    source_entities = [{"id": "ws-3", "name": "legacy", "project_id": None, "organization": "org-1"}]
    with _patch_source(source_data):
        result = select_entities(db, batch["id"], "workspaces", ["ws-3"], source_entities)
    entities = get_batch_entities(db, batch["id"])
    # Should have ws-3 + org-1 (as organizations, not projects)
    org_entity = next((e for e in entities if e["entity_id"] == "org-1"), None)
    assert org_entity is not None, "org-1 should be auto-included"
    assert org_entity["entity_type"] == "organizations", "parent should be organizations, not projects"
    assert result["auto_added"] == 1


def test_extract_parent_id_json_api_format() -> None:
    """_extract_parent_id reads JSON API relationships.project.data.id."""
    from smk.core.db.entities import _extract_parent_id

    entity = {"relationships": {"project": {"data": {"id": "prj-99"}}}}
    assert _extract_parent_id(entity, "workspaces") == "prj-99"


def test_load_source_entity_missing_file(tmp_path: Path) -> None:
    """_load_source_entity returns None when source file missing."""
    from smk.core.db.entities import _load_source_entity

    with patch("smk.core.db.entities._get_source_dir", return_value=tmp_path):
        result = _load_source_entity("workspaces", "ws-1")
    assert result is None


def test_get_source_dir_returns_path() -> None:
    """_get_source_dir returns a Path without raising."""
    from smk.core.db.entities import _get_source_dir

    result = _get_source_dir()
    assert str(result).endswith("source")
