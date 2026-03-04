"""Migration API routes."""

import asyncio
import logging
import sqlite3
from typing import Any

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel

from smk.core.config.manager import ConfigManager
from smk.core.config.paths import get_data_dir, get_output_dir
from smk.core.db import get_db
from smk.core.db.batches import confirm_batch, create_batch, get_batch_stats, get_current_batch
from smk.core.db.entities import deselect_entities, get_batch_entities, list_entities, select_entities

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/migrate", tags=["migrate"])


def _get_db(request: Request) -> sqlite3.Connection:
    """Get the DB connection using the config dir from app state."""
    config = getattr(request.app.state, "web_config", None)
    config_dir = getattr(config, "config_dir", None) if config else None
    return get_db(config_dir)


def _get_source_plugin() -> str:
    """Return the active source plugin id."""
    from smk.core.exceptions import ConfigNotInitializedError

    manager = ConfigManager()
    try:
        cfg = manager.load()
        return cfg.source.plugin or ""
    except ConfigNotInitializedError:
        return ""


def _load_source_entities(entity_type: str) -> list[dict[str, Any]]:
    """Load raw source entities from disk."""
    import json

    path = get_data_dir(subdir="source") / f"{entity_type}.json"
    if not path.exists():
        return []
    return json.loads(path.read_text())


# ── Batch endpoints ───────────────────────────────────────────────────────────


@router.get("/batch/current")
async def get_current_batch_endpoint(request: Request) -> dict[str, Any]:
    """Return active draft batch with stats, or empty dict if none."""
    db = await asyncio.to_thread(_get_db, request)
    try:
        batch = await asyncio.to_thread(get_current_batch, db)
        if batch is None:
            return {}
        stats = await asyncio.to_thread(get_batch_stats, db, batch["id"])
        return {**batch, "stats": stats}
    finally:
        db.close()


@router.post("/batch", status_code=201)
async def create_batch_endpoint(request: Request) -> dict[str, Any]:
    """Create a new batch. Returns 409 if a draft already exists."""
    db = await asyncio.to_thread(_get_db, request)
    try:
        try:
            batch = await asyncio.to_thread(create_batch, db)
        except ValueError as e:
            raise HTTPException(status_code=409, detail=str(e)) from e
        return batch
    finally:
        db.close()


@router.delete("/batch/{batch_id}", status_code=200)
async def discard_batch(batch_id: int, request: Request) -> dict[str, Any]:
    """Discard a draft batch. Returns 400 if not draft."""
    db = await asyncio.to_thread(_get_db, request)
    try:
        row = db.execute("SELECT * FROM batches WHERE id = ?", (batch_id,)).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail=f"Batch #{batch_id} not found")
        if dict(row)["status"] != "draft":
            raise HTTPException(status_code=400, detail=f"Batch #{batch_id} is not a draft")
        db.execute("DELETE FROM batches WHERE id = ?", (batch_id,))
        db.commit()
        return {"deleted": True, "batch_id": batch_id}
    finally:
        db.close()


# ── Entity endpoints ──────────────────────────────────────────────────────────


@router.get("/entities")
async def list_entities_endpoint(
    request: Request,
    type: str = Query("workspaces", alias="type"),  # noqa: A002
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    search: str = Query(""),
    filter: str = Query("all", alias="filter"),  # noqa: A002
) -> dict[str, Any]:
    """List entities with pagination, search, and filter."""
    db = await asyncio.to_thread(_get_db, request)
    try:
        result = await asyncio.to_thread(list_entities, db, type, page, per_page, search, filter)
        return result
    finally:
        db.close()


class SelectRequest(BaseModel):
    entity_type: str
    entity_ids: list[str]
    selected: bool = True


@router.post("/entities/select")
async def select_entities_endpoint(body: SelectRequest, request: Request) -> dict[str, Any]:
    """Select or deselect entities in the current draft batch."""
    db = await asyncio.to_thread(_get_db, request)
    try:
        batch = await asyncio.to_thread(get_current_batch, db)
        if batch is None:
            # Auto-create a batch
            batch = await asyncio.to_thread(create_batch, db)

        batch_id = batch["id"]

        if not body.selected:
            removed = await asyncio.to_thread(deselect_entities, db, batch_id, body.entity_type, body.entity_ids)
            return {"removed": removed}

        source_entities = await asyncio.to_thread(_load_source_entities, body.entity_type)
        result = await asyncio.to_thread(
            select_entities, db, batch_id, body.entity_type, body.entity_ids, source_entities
        )
        return result
    finally:
        db.close()


# ── Transform endpoints ───────────────────────────────────────────────────────


@router.post("/batch/{batch_id}/transform")
async def start_transform(batch_id: int, request: Request) -> dict[str, Any]:
    """Start async transform for all selected entities in the batch."""
    db = await asyncio.to_thread(_get_db, request)
    try:
        row = db.execute("SELECT * FROM batches WHERE id = ?", (batch_id,)).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail=f"Batch #{batch_id} not found")
        if dict(row)["status"] != "draft":
            raise HTTPException(status_code=400, detail=f"Batch #{batch_id} is not a draft")
        source_plugin = _get_source_plugin()
        plugin_manager = request.app.state.plugin_manager
        await asyncio.to_thread(plugin_manager.transform_batch, batch_id, source_plugin, db)
        stats = await asyncio.to_thread(get_batch_stats, db, batch_id)
        return stats
    finally:
        db.close()


@router.get("/batch/{batch_id}/entities")
async def get_batch_entities_endpoint(batch_id: int, request: Request) -> list[dict[str, Any]]:
    """Return all entities in a batch with full data (source_entity, spacelift_entity, etc.)."""
    db = await asyncio.to_thread(_get_db, request)
    try:
        return await asyncio.to_thread(get_batch_entities, db, batch_id)
    finally:
        db.close()


@router.get("/batch/{batch_id}/transform/status")
async def transform_status(batch_id: int, request: Request) -> dict[str, Any]:
    """Return transform status counts for a batch."""
    db = await asyncio.to_thread(_get_db, request)
    try:
        stats = await asyncio.to_thread(get_batch_stats, db, batch_id)
        return stats
    finally:
        db.close()


# ── Confirm endpoint ──────────────────────────────────────────────────────────


@router.post("/batch/{batch_id}/confirm")
async def confirm_batch_endpoint(batch_id: int, request: Request) -> dict[str, Any]:
    """Write HCL and mark batch confirmed."""
    from smk.core.hcl import batch_to_hcl

    db = await asyncio.to_thread(_get_db, request)
    try:
        row = db.execute("SELECT * FROM batches WHERE id = ?", (batch_id,)).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail=f"Batch #{batch_id} not found")
        if dict(row)["status"] != "draft":
            raise HTTPException(status_code=400, detail=f"Batch #{batch_id} is not a draft")

        entities = await asyncio.to_thread(get_batch_entities, db, batch_id, "ready")
        if not entities:
            raise HTTPException(status_code=400, detail="No ready entities to confirm")

        # Parse spacelift_entity JSON
        import json

        parsed = [json.loads(e["spacelift_entity"]) for e in entities if e.get("spacelift_entity")]

        hcl_content = await asyncio.to_thread(batch_to_hcl, batch_id, parsed)

        output_dir = get_output_dir()
        output_dir.mkdir(parents=True, exist_ok=True)
        hcl_path = output_dir / f"batch-{batch_id:03d}.tf"
        hcl_path.write_text(hcl_content)

        await asyncio.to_thread(confirm_batch, db, batch_id)

        return {
            "hcl_path": str(hcl_path),
            "batch_id": batch_id,
            "entity_count": len(parsed),
        }
    finally:
        db.close()
