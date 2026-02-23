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


@router.get("/export/status")
async def export_status() -> dict[str, Any]:
    """Return whether source data has already been exported."""
    data_dir = get_data_dir(subdir="source")
    keys = ["organizations", "projects", "workspaces"]
    if not all((data_dir / f"{k}.json").exists() for k in keys):
        return {"exported": False}
    counts = {k: len(orjson.loads((data_dir / f"{k}.json").read_bytes())) for k in keys}
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
