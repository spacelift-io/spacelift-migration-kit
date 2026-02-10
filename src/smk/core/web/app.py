"""FastAPI application factory."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from jinja2 import Environment, FileSystemLoader

from smk.core.web.config import WebConfig

WEB_DIR = Path(__file__).parent
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

    app = FastAPI(
        debug=config.debug,
        title="SMK Web Interface",
    )

    # Store config in app state
    app.state.config = config

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
    from smk.core.web.routes.pages import router as pages_router
    from smk.core.web.routes.partials import router as partials_router

    app.include_router(api_router)
    app.include_router(pages_router)
    app.include_router(partials_router)

    return app
