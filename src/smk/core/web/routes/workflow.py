"""Workflow routes for migration wizard."""

import contextlib

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from smk.core.config.manager import ConfigManager
from smk.core.exceptions import ConfigNotInitializedError

router = APIRouter(tags=["workflow"])

# Workflow step definitions
WORKFLOW_STEPS = [
    {"id": "start", "name": "Start", "icon": "home"},
    {"id": "configure", "name": "Configure", "number": 1},
    {"id": "export", "name": "Export", "number": 2},
    {"id": "audit", "name": "Audit", "number": 3},
    {"id": "migrate", "name": "Migrate", "number": 4},
    {"id": "cleanup", "name": "Clean Up", "number": 5},
    {"id": "complete", "name": "Wrap Up", "number": 6},
]


def _get_workflow_context(current_step: str) -> dict:
    """Build context data for workflow templates.

    Args:
        current_step: ID of current step

    Returns:
        Dictionary with workflow context including stepper data and navigation
    """
    step_ids = [step["id"] for step in WORKFLOW_STEPS]
    current_index = step_ids.index(current_step)

    # Steps before current are completed
    completed_steps = step_ids[:current_index]

    # Calculate next and previous steps
    prev_step = step_ids[current_index - 1] if current_index > 0 else None
    next_step = step_ids[current_index + 1] if current_index < len(step_ids) - 1 else None

    return {
        "current_step": current_step,
        "completed_steps": completed_steps,
        "next_step": next_step,
        "prev_step": prev_step,
        "workflow_steps": WORKFLOW_STEPS,
    }


def _save_last_step(step: str) -> None:
    """Save the last visited workflow step, silently ignoring errors.

    Args:
        step: The step ID to save.
    """
    with contextlib.suppress(Exception):
        ConfigManager().save_last_step(step)


@router.get("/", response_class=HTMLResponse, response_model=None)
async def workflow_root(request: Request) -> HTMLResponse | RedirectResponse:
    """Redirect to last visited step, or render start page."""
    last_step = ConfigManager().load_last_step()
    if last_step != "start":
        return RedirectResponse(url=f"/{last_step}")
    templates = request.app.state.templates
    context = _get_workflow_context("start")
    context["request"] = request
    template = templates.get_template("pages/workflow/start.html")
    return HTMLResponse(template.render(**context))


@router.get("/start", response_class=HTMLResponse)
async def workflow_start(request: Request) -> HTMLResponse:
    """Render the workflow start page."""
    templates = request.app.state.templates
    context = _get_workflow_context("start")
    context["request"] = request
    last_step = ConfigManager().load_last_step()
    if last_step != "start":
        step_names = {step["id"]: step["name"] for step in WORKFLOW_STEPS}
        context["resume_step"] = last_step
        context["resume_step_name"] = step_names.get(last_step, last_step)
    else:
        context["resume_step"] = None
        context["resume_step_name"] = None
    template = templates.get_template("pages/workflow/start.html")
    return HTMLResponse(template.render(**context))


@router.get("/configure", response_class=HTMLResponse)
async def workflow_configure(request: Request) -> HTMLResponse:
    """Render the workflow configure page."""
    _save_last_step("configure")
    templates = request.app.state.templates
    context = _get_workflow_context("configure")
    context["request"] = request
    context["source_plugins"] = sorted(
        request.app.state.plugin_manager.get_source_plugins(),
        key=lambda p: p["display_name"],
    )
    try:
        config = ConfigManager().load()
        context["current_config"] = config.model_dump()
    except ConfigNotInitializedError:
        context["current_config"] = None
    template = templates.get_template("pages/workflow/configure.html")
    return HTMLResponse(template.render(**context))


@router.get("/export", response_class=HTMLResponse)
async def workflow_export(request: Request) -> HTMLResponse:
    """Render the workflow export page."""
    _save_last_step("export")
    templates = request.app.state.templates
    context = _get_workflow_context("export")
    context["request"] = request
    template = templates.get_template("pages/workflow/export.html")
    return HTMLResponse(template.render(**context))


@router.get("/audit", response_class=HTMLResponse)
async def workflow_audit(request: Request) -> HTMLResponse:
    """Render the workflow audit page."""
    _save_last_step("audit")
    templates = request.app.state.templates
    context = _get_workflow_context("audit")
    context["request"] = request
    template = templates.get_template("pages/workflow/audit.html")
    return HTMLResponse(template.render(**context))


@router.get("/migrate", response_class=HTMLResponse)
async def workflow_migrate(request: Request) -> HTMLResponse:
    """Render the workflow migrate page."""
    _save_last_step("migrate")
    templates = request.app.state.templates
    context = _get_workflow_context("migrate")
    context["request"] = request
    template = templates.get_template("pages/workflow/migrate.html")
    return HTMLResponse(template.render(**context))


@router.get("/cleanup", response_class=HTMLResponse)
async def workflow_cleanup(request: Request) -> HTMLResponse:
    """Render the workflow cleanup page."""
    _save_last_step("cleanup")
    templates = request.app.state.templates
    context = _get_workflow_context("cleanup")
    context["request"] = request
    template = templates.get_template("pages/workflow/cleanup.html")
    return HTMLResponse(template.render(**context))


@router.get("/complete", response_class=HTMLResponse)
async def workflow_complete(request: Request) -> HTMLResponse:
    """Render the workflow complete page."""
    _save_last_step("complete")
    templates = request.app.state.templates
    context = _get_workflow_context("complete")
    context["request"] = request
    template = templates.get_template("pages/workflow/complete.html")
    return HTMLResponse(template.render(**context))
