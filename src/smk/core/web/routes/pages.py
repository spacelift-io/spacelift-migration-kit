"""Full page routes."""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from smk.core.config.manager import ConfigManager
from smk.core.exceptions import ConfigNotInitializedError

router = APIRouter(tags=["pages"])


@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request) -> HTMLResponse:
    """Render the dashboard page."""
    templates = request.app.state.templates
    template = templates.get_template("pages/dashboard.html")
    return HTMLResponse(template.render(request=request))


@router.get("/config", response_class=HTMLResponse)
async def config_page(request: Request) -> HTMLResponse:
    """Render the configuration page."""
    templates = request.app.state.templates
    manager = ConfigManager()

    config = None
    config_initialized = manager.is_initialized
    if config_initialized:
        try:
            config = manager.load()
        except ConfigNotInitializedError:
            config_initialized = False

    template = templates.get_template("pages/config.html")
    return HTMLResponse(
        template.render(
            config=config,
            config_initialized=config_initialized,
            request=request,
        )
    )


@router.get("/plugins", response_class=HTMLResponse)
async def plugins_page(request: Request) -> HTMLResponse:
    """Render the plugins page."""
    templates = request.app.state.templates
    plugin_manager = request.app.state.plugin_manager

    loaded_plugins = plugin_manager.get_loaded_plugins()
    failed_plugins = plugin_manager.get_failed_plugins()
    is_bundled = plugin_manager.is_bundled
    is_dev_mode = plugin_manager.is_development_mode()

    template = templates.get_template("pages/plugins.html")
    return HTMLResponse(
        template.render(
            loaded_plugins=loaded_plugins,
            failed_plugins=failed_plugins,
            is_bundled=is_bundled,
            is_dev_mode=is_dev_mode,
            request=request,
        )
    )
