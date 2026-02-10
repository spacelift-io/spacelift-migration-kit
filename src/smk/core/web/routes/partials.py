"""HTMX partial routes."""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from smk.core.config.manager import ConfigManager

router = APIRouter(prefix="/partials", tags=["partials"])


@router.get("/config-status", response_class=HTMLResponse)
async def config_status(request: Request) -> HTMLResponse:
    """Return config status partial for HTMX."""
    templates = request.app.state.templates
    manager = ConfigManager()

    template = templates.get_template("partials/_config_status.html")
    return HTMLResponse(
        template.render(
            config_file=str(manager.config_file),
            config_initialized=manager.is_initialized,
        )
    )
