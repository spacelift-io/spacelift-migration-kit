"""Entity CRUD, pagination, and auto-dependency resolution."""

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from smk.core.config.paths import get_data_dir

# Maps entity_type → default parent_type.
# workspaces can fall back to "organizations" when project_id is absent.
_PARENT_MAP: dict[str, str | None] = {
    "organizations": None,
    "projects": "organizations",
    "workspaces": "projects",
}


def list_entities(
    db: sqlite3.Connection,
    entity_type: str,
    page: int = 1,
    per_page: int = 50,
    search: str = "",
    filter_: str = "all",
) -> dict[str, Any]:
    """List entities with pagination, search, and filter.

    Args:
        db: Database connection.
        entity_type: Entity type to list (organizations, projects, workspaces).
        page: 1-based page number.
        per_page: Items per page.
        search: Search string matched against entity_name.
        filter_: 'all' | 'selected' | 'unselected' | 'migrated'

    Returns:
        Dict with items, total, page, per_page.
    """
    source_dir = _get_source_dir()
    source_path = source_dir / f"{entity_type}.json"
    if not source_path.exists():
        return {"items": [], "total": 0, "page": page, "per_page": per_page}

    raw_entities: list[dict[str, Any]] = json.loads(source_path.read_text())

    # Build a lookup of entity_id → batch info from DB
    db_rows = db.execute(
        """
        SELECT be.entity_id, be.status AS raw_batch_status, be.auto_included, b.status AS batch_status
        FROM batch_entities be
        JOIN batches b ON b.id = be.batch_id
        WHERE be.entity_type = ?
        """,
        (entity_type,),
    ).fetchall()

    db_lookup: dict[str, dict[str, Any]] = {}
    for row in db_rows:
        effective = "migrated" if row["batch_status"] == "confirmed" else row["raw_batch_status"]
        db_lookup[row["entity_id"]] = {
            "batch_status": effective,
            "auto_included": bool(row["auto_included"]),
        }

    # Build result items
    items: list[dict[str, Any]] = []
    for entity in raw_entities:
        eid = entity.get("id", "")
        name = _extract_name(entity)
        parent_id, parent_name = _extract_parent(entity, entity_type)

        db_info = db_lookup.get(eid)
        batch_status = db_info["batch_status"] if db_info else None
        auto_included = db_info["auto_included"] if db_info else False

        # Apply filter
        if filter_ == "selected" and batch_status not in ("selected", "transforming", "ready", "error"):
            continue
        if filter_ == "unselected" and batch_status is not None:
            continue
        if filter_ == "migrated" and batch_status != "migrated":
            continue
        if filter_ == "unmigrated" and batch_status == "migrated":
            continue

        # Apply search
        if search and search.lower() not in name.lower() and search.lower() not in eid.lower():
            continue

        items.append(
            {
                "entity_id": eid,
                "entity_name": name,
                "parent_id": parent_id,
                "parent_name": parent_name,
                "batch_status": batch_status,
                "auto_included": auto_included,
            }
        )

    total = len(items)
    offset = (page - 1) * per_page
    page_items = items[offset : offset + per_page]

    return {"items": page_items, "total": total, "page": page, "per_page": per_page}


def select_entities(
    db: sqlite3.Connection,
    batch_id: int,
    entity_type: str,
    entity_ids: list[str],
    source_entities: list[dict[str, Any]],
) -> dict[str, Any]:
    """Select entities into the batch with auto-dependency resolution.

    Returns:
        Dict with added, auto_added, already_migrated counts.
    """
    added = 0
    auto_added = 0
    already_migrated = 0

    # Build a lookup of id → entity from the provided source list
    entity_lookup: dict[str, dict[str, Any]] = {e.get("id", ""): e for e in source_entities}

    # Check which are already migrated (in a confirmed batch)
    for eid in entity_ids:
        row = db.execute(
            """
            SELECT be.status, b.status AS batch_status
            FROM batch_entities be
            JOIN batches b ON b.id = be.batch_id
            WHERE be.entity_type = ? AND be.entity_id = ?
            """,
            (entity_type, eid),
        ).fetchone()
        if row and row["batch_status"] == "confirmed":
            already_migrated += 1
            continue

        entity = entity_lookup.get(eid, {"id": eid})
        name = _extract_name(entity)
        parent_type = _extract_parent_type(entity, entity_type)
        parent_id = _extract_parent_id(entity, entity_type)

        result = _upsert_entity(
            db,
            batch_id=batch_id,
            entity_type=entity_type,
            entity_id=eid,
            entity_name=name,
            parent_type=parent_type,
            parent_id=parent_id,
            auto_included=False,
            source_entity=entity,
        )
        if result:
            added += 1

        # Auto-include parent if needed
        if parent_type and parent_id:
            auto_added += _auto_include_parent(
                db,
                batch_id=batch_id,
                parent_type=parent_type,
                parent_id=parent_id,
            )
            # Recurse one level up (workspace → project → org)
            grandparent_type = _PARENT_MAP.get(parent_type)
            if grandparent_type:
                parent_entity = _load_source_entity(parent_type, parent_id)
                grandparent_id = _extract_parent_id(parent_entity, parent_type) if parent_entity else None
                if grandparent_id:
                    auto_added += _auto_include_parent(
                        db,
                        batch_id=batch_id,
                        parent_type=grandparent_type,
                        parent_id=grandparent_id,
                    )

    db.commit()
    return {"added": added, "auto_added": auto_added, "already_migrated": already_migrated}


def deselect_entities(
    db: sqlite3.Connection,
    batch_id: int,
    entity_type: str,
    entity_ids: list[str],
) -> int:
    """Remove entities from the batch. Returns count removed."""
    count = 0
    for eid in entity_ids:
        cursor = db.execute(
            "DELETE FROM batch_entities WHERE batch_id = ? AND entity_type = ? AND entity_id = ?",
            (batch_id, entity_type, eid),
        )
        count += cursor.rowcount
    db.commit()
    return count


def get_batch_entities(
    db: sqlite3.Connection,
    batch_id: int,
    status: str | None = None,
) -> list[dict[str, Any]]:
    """Return all entities in a batch, optionally filtered by status."""
    if status:
        rows = db.execute(
            "SELECT * FROM batch_entities WHERE batch_id = ? AND status = ? ORDER BY entity_type, entity_name",
            (batch_id, status),
        ).fetchall()
    else:
        rows = db.execute(
            "SELECT * FROM batch_entities WHERE batch_id = ? ORDER BY entity_type, entity_name",
            (batch_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def update_entity_transform(
    db: sqlite3.Connection,
    batch_id: int,
    entity_type: str,
    entity_id: str,
    *,
    spacelift_entity: dict[str, Any],
    hcl_resource_name: str,
) -> None:
    """Update entity after successful transform."""
    db.execute(
        """
        UPDATE batch_entities
        SET status = 'ready',
            spacelift_entity = ?,
            hcl_resource_name = ?,
            error_message = NULL,
            transformed_at = ?
        WHERE batch_id = ? AND entity_type = ? AND entity_id = ?
        """,
        (
            json.dumps(spacelift_entity),
            hcl_resource_name,
            datetime.now(timezone.utc).isoformat(),
            batch_id,
            entity_type,
            entity_id,
        ),
    )
    db.commit()


def update_entity_error(
    db: sqlite3.Connection,
    batch_id: int,
    entity_type: str,
    entity_id: str,
    error: str,
) -> None:
    """Update entity with error from failed transform."""
    db.execute(
        """
        UPDATE batch_entities
        SET status = 'error', error_message = ?
        WHERE batch_id = ? AND entity_type = ? AND entity_id = ?
        """,
        (error, batch_id, entity_type, entity_id),
    )
    db.commit()


# ── internal helpers ──────────────────────────────────────────────────────────


def _get_source_dir() -> Path:
    return get_data_dir(subdir="source")


def _extract_name(entity: dict[str, Any]) -> str:
    """Extract display name from a raw entity dict.

    Handles both flat pytfe model format (direct 'name' field) and
    JSON API format (attributes.name).
    """
    name = entity.get("name") or entity.get("attributes", {}).get("name")
    return name or entity.get("id", "")


def _extract_parent_type(entity: dict[str, Any], entity_type: str) -> str | None:
    """Determine actual parent entity type, accounting for workspace fallback.

    When a workspace has no project_id, its parent is an organization, not a project.
    """
    if entity_type != "workspaces":
        return _PARENT_MAP.get(entity_type)
    # Workspace with an explicit project_id → parent is a project
    if entity.get("project_id"):
        return "projects"
    # JSON API workspace with a project relationship → parent is a project
    rels = entity.get("relationships", {})
    if rels.get("project", {}).get("data", {}).get("id"):
        return "projects"
    if entity.get("attributes", {}).get("project-id"):
        return "projects"
    # No project — workspace is directly under an org
    if entity.get("organization"):
        return "organizations"
    return "projects"  # default fallback


def _extract_parent_id(entity: dict[str, Any], entity_type: str) -> str | None:
    """Extract parent ID from a raw entity dict.

    Handles both flat pytfe model format and JSON API format.
    pytfe flat format:
      - workspace: project_id (may be None), organization (org name)
      - project: organization (org name/id)
    JSON API format:
      - workspace: relationships.project.data.id, attributes.project-id
      - project: relationships.organization.data.id
    """
    if entity_type == "workspaces":
        # Flat pytfe format: project_id is direct field
        pid = entity.get("project_id")
        if pid:
            return str(pid)
        # Flat pytfe: fall back to organization
        org = entity.get("organization")
        if org:
            return str(org)
        # JSON API format
        rels = entity.get("relationships", {})
        proj = rels.get("project", {}).get("data", {})
        pid = proj.get("id") if proj else None
        if pid:
            return str(pid)
        return entity.get("attributes", {}).get("project-id")
    if entity_type == "projects":
        # Flat pytfe format: organization is direct field
        org = entity.get("organization")
        if org:
            return str(org)
        # JSON API format
        rels = entity.get("relationships", {})
        org_data = rels.get("organization", {}).get("data", {})
        return org_data.get("id") if org_data else None
    return None


def _extract_parent(
    entity: dict[str, Any],
    entity_type: str,
) -> tuple[str | None, str | None]:
    """Return (parent_id, parent_name) for display."""
    parent_id = _extract_parent_id(entity, entity_type)
    if not parent_id:
        return None, None
    parent_type = _extract_parent_type(entity, entity_type)
    if not parent_type:  # pragma: no cover
        return parent_id, parent_id
    parent_entity = _load_source_entity(parent_type, parent_id)
    parent_name = _extract_name(parent_entity) if parent_entity else parent_id
    return parent_id, parent_name


def _load_source_entity(entity_type: str, entity_id: str) -> dict[str, Any] | None:
    """Load a single entity from the source data files."""
    source_path = _get_source_dir() / f"{entity_type}.json"
    if not source_path.exists():
        return None
    entities: list[dict[str, Any]] = json.loads(source_path.read_text())
    for e in entities:
        if e.get("id") == entity_id:
            return e
    return None


def _upsert_entity(
    db: sqlite3.Connection,
    *,
    batch_id: int,
    entity_type: str,
    entity_id: str,
    entity_name: str,
    parent_type: str | None,
    parent_id: str | None,
    auto_included: bool,
    source_entity: dict[str, Any],
) -> bool:
    """Insert entity into batch; return True if inserted, False if already present."""
    # Check if already in this batch or any batch
    existing = db.execute(
        "SELECT batch_id FROM batch_entities WHERE entity_type = ? AND entity_id = ?",
        (entity_type, entity_id),
    ).fetchone()
    if existing is not None:
        return False
    db.execute(
        """
        INSERT INTO batch_entities
            (batch_id, entity_type, entity_id, entity_name, parent_type, parent_id,
             auto_included, status, source_entity)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'selected', ?)
        """,
        (
            batch_id,
            entity_type,
            entity_id,
            entity_name,
            parent_type,
            parent_id,
            1 if auto_included else 0,
            json.dumps(source_entity),
        ),
    )
    return True


def _auto_include_parent(
    db: sqlite3.Connection,
    *,
    batch_id: int,
    parent_type: str,
    parent_id: str,
) -> int:
    """Auto-include a parent entity if not already in a confirmed batch or this batch.

    Returns 1 if auto-included, 0 otherwise.
    """
    # Check if already migrated (in confirmed batch)
    existing = db.execute(
        """
        SELECT be.batch_id, b.status AS batch_status
        FROM batch_entities be
        JOIN batches b ON b.id = be.batch_id
        WHERE be.entity_type = ? AND be.entity_id = ?
        """,
        (parent_type, parent_id),
    ).fetchone()

    if existing is not None:
        # Already in a confirmed batch or current batch — no need to add
        return 0

    parent_entity = _load_source_entity(parent_type, parent_id)
    entity = parent_entity or {"id": parent_id}
    name = _extract_name(entity)
    grandparent_type = _PARENT_MAP.get(parent_type)
    grandparent_id = _extract_parent_id(entity, parent_type)

    inserted = _upsert_entity(
        db,
        batch_id=batch_id,
        entity_type=parent_type,
        entity_id=parent_id,
        entity_name=name,
        parent_type=grandparent_type,
        parent_id=grandparent_id,
        auto_included=True,
        source_entity=entity,
    )
    return 1 if inserted else 0
