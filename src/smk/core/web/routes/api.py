"""JSON API routes."""

import asyncio
import logging
from typing import Any

import orjson
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from smk.core.config.manager import ConfigManager
from smk.core.config.paths import get_data_dir
from smk.core.exceptions import ConfigNotInitializedError

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["api"])


@router.get("/health")
async def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}


@router.get("/audit/status")
async def audit_status(request: Request) -> dict[str, Any]:
    """Return cached audit results."""
    data_dir = get_data_dir(subdir="source")
    path = data_dir / "audit_results.json"
    if not path.exists():
        return {"audited": False}
    manager = ConfigManager()
    try:
        config = manager.load()
    except ConfigNotInitializedError:
        return {"audited": False}
    entity_types = request.app.state.plugin_manager.get_entity_types(config.source.plugin)
    issues = orjson.loads(path.read_bytes())
    return {"audited": True, "entity_types": entity_types, "issues": issues}


@router.get("/entity-types")
async def get_entity_types(request: Request) -> list[dict]:
    """Return entity types for the configured source plugin."""
    manager = ConfigManager()
    try:
        config = manager.load()
    except ConfigNotInitializedError:
        return []
    return request.app.state.plugin_manager.get_entity_types(config.source.plugin)


@router.get("/export/status")
async def export_status(request: Request) -> dict[str, Any]:
    """Return whether source data has already been exported."""
    manager = ConfigManager()
    if not manager.is_initialized:
        return {"exported": False}
    try:
        config = manager.load()
    except ConfigNotInitializedError:
        return {"exported": False}
    source_plugin = config.source.plugin
    entity_types = request.app.state.plugin_manager.get_entity_types(source_plugin)
    data_dir = get_data_dir(subdir="source")
    if not entity_types or not all((data_dir / f"{et['id']}.json").exists() for et in entity_types):
        return {"exported": False}
    counts = {et["id"]: len(orjson.loads((data_dir / f"{et['id']}.json").read_bytes())) for et in entity_types}
    return {"exported": True, **counts}


@router.get("/config/status")
async def config_status() -> dict[str, Any]:
    """Return configuration status."""
    manager = ConfigManager()
    return {
        "config_file": str(manager.config_file),
        "initialized": manager.is_initialized,
    }


@router.get("/config")
async def get_config() -> dict[str, Any]:
    """Return current configuration."""
    manager = ConfigManager()
    try:
        config = manager.load()
        return {
            "config_version": config.config_version,
            "source": {
                "plugin": config.source.plugin,
            },
            "spacelift": {
                "api_endpoint": config.spacelift.api_endpoint,
                "api_key_id": config.spacelift.api_key_id,
                "has_secret": config.spacelift.api_key_secret is not None,
            },
        }
    except ConfigNotInitializedError:
        return {"error": "Configuration not initialized"}


@router.get("/logs")
async def list_log_files(request: Request) -> list[dict[str, Any]]:
    """Return list of available log files."""
    current = request.app.state.log_file
    all_files = sorted(current.parent.glob("smk-*.log"), key=lambda f: f.name, reverse=True)
    return [{"name": f.name, "current": f == current} for f in sorted(all_files, key=lambda f: f != current)]


@router.get("/plugins/sources")
async def get_source_plugins(request: Request) -> list[dict]:
    """Return metadata for all registered source plugins."""
    return request.app.state.plugin_manager.get_source_plugins()


class SaveConfigRequest(BaseModel):
    source_plugin: str | None = None
    source_credentials: dict[str, str] = {}
    spacelift_api_endpoint: str | None = None
    spacelift_api_key_id: str | None = None
    spacelift_api_key_secret: str | None = None


@router.post("/audit")
async def run_audit(request: Request) -> dict[str, Any]:
    """Run audit for all entity types. Returns {entity_type_id: [issues]}."""
    manager = ConfigManager()
    try:
        config = manager.load()
    except ConfigNotInitializedError as e:
        raise HTTPException(status_code=400, detail="Configuration not initialized") from e
    plugin_manager = request.app.state.plugin_manager
    entity_types = plugin_manager.get_entity_types(config.source.plugin)
    try:
        results = await asyncio.to_thread(plugin_manager.run_audit, config.source.plugin, entity_types)
    except Exception as e:
        logger.error("Audit failed: %s", e)
        raise HTTPException(status_code=502, detail=str(e)) from e
    data_dir = get_data_dir(subdir="source")
    data_dir.mkdir(parents=True, exist_ok=True)
    (data_dir / "audit_results.json").write_bytes(orjson.dumps(results))
    return {"entity_types": entity_types, "issues": results}


@router.post("/export")
async def run_export(request: Request) -> dict[str, Any]:
    """Run the source plugin export and return entity counts."""
    manager = ConfigManager()
    try:
        config = manager.load()
    except ConfigNotInitializedError as e:
        raise HTTPException(status_code=400, detail="Configuration not initialized") from e

    vendor_config = {
        "credentials": dict(config.source.credentials),
        "source_plugin": config.source.plugin,
    }
    plugin_manager = request.app.state.plugin_manager
    try:
        results = await asyncio.to_thread(plugin_manager.pm.hook.smk_export_data, vendor_config=vendor_config)
    except Exception as e:
        logger.error("Export failed: %s", e)
        raise HTTPException(status_code=502, detail=str(e)) from e
    return next((r for r in results if r is not None), {})


@router.post("/config")
async def save_config(body: SaveConfigRequest) -> dict[str, str]:
    """Save configuration from the configure page."""
    ConfigManager().init(
        force=True,
        source_credentials=body.source_credentials,
        source_plugin=body.source_plugin,
        spacelift_endpoint=body.spacelift_api_endpoint,
        spacelift_key_id=body.spacelift_api_key_id,
        spacelift_key_secret=body.spacelift_api_key_secret,
    )
    return {"status": "saved"}
