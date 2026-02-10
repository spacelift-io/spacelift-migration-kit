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
