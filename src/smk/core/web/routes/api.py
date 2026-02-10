"""JSON API routes."""

from typing import Any

from fastapi import APIRouter

from smk.core.config.manager import ConfigManager
from smk.core.exceptions import ConfigNotInitializedError

router = APIRouter(prefix="/api", tags=["api"])


@router.get("/health")
async def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}


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
