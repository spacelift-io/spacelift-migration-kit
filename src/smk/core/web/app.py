"""FastAPI application factory."""

import logging
import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from jinja2 import Environment, FileSystemLoader

from smk.core.web.config import WebConfig

logger = logging.getLogger(__name__)

try:
    from arel import HotReload
    from arel._models import Path as ArelPath
except (ImportError, AssertionError):
    # ImportError: arel not installed
    # AssertionError: arel doesn't work with PyInstaller bundling
    HotReload = None  # type: ignore[assignment,misc]
    ArelPath = None  # type: ignore[assignment,misc]


def _get_resource_path() -> Path:
    """Get path to resources, handling frozen executables.

    Returns:
        Path to web module directory, accounting for PyInstaller's _MEIPASS.
    """
    if getattr(sys, "frozen", False):
        # Running as compiled executable
        return Path(sys._MEIPASS) / "smk" / "core" / "web"  # type: ignore[attr-defined]
    else:
        # Running as normal Python
        return Path(__file__).parent


WEB_DIR = _get_resource_path()
STATIC_DIR = WEB_DIR / "static"
TEMPLATES_DIR = WEB_DIR / "templates"


def create_app(config: WebConfig | None = None) -> FastAPI:
    """Create and configure the FastAPI application.

    Args:
        config: Web server configuration. Uses defaults if None.

    Returns:
        Configured FastAPI application.
    """
    if config is None:
        config = WebConfig()

    # Set up file logging before plugin loading so plugin events are captured
    from smk.core.config.manager import ConfigManager
    from smk.core.logging import setup_logging

    log_file = setup_logging(ConfigManager().logs_dir, debug=config.debug)

    app = FastAPI(
        debug=config.debug,
        title="SMK Web Interface",
    )

    # Store config and log file path in app state
    app.state.config = config
    app.state.log_file = log_file  # SSE endpoint will tail this path

    logger.info("SMK web application starting (debug=%s)", config.debug)

    # Initialize plugin manager
    from smk.core.plugins import SMKPluginManager

    plugin_manager = SMKPluginManager()
    plugin_manager.initialize()
    app.state.plugin_manager = plugin_manager

    # Set up Jinja2 templates
    template_env = Environment(
        autoescape=True,
        loader=FileSystemLoader(TEMPLATES_DIR),
    )
    app.state.templates = template_env

    # Mount static files
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    # Include routers
    from smk.core.web.routes.api import router as api_router
    from smk.core.web.routes.partials import router as partials_router
    from smk.core.web.routes.workflow import router as workflow_router

    app.include_router(api_router)
    app.include_router(workflow_router)
    app.include_router(partials_router)

    # Set up hot reload in debug mode
    if config.debug and HotReload is not None and ArelPath is not None:
        hot_reload = HotReload(
            paths=[
                ArelPath(path=str(TEMPLATES_DIR)),
                ArelPath(path=str(STATIC_DIR)),
            ]
        )
        app.add_event_handler("startup", hot_reload.startup)
        app.add_event_handler("shutdown", hot_reload.shutdown)
        app.add_websocket_route("/hot-reload", hot_reload)  # type: ignore[arg-type]
        app.state.hot_reload = hot_reload
    else:
        app.state.hot_reload = None

    return app
