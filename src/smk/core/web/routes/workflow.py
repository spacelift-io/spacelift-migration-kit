"""Workflow routes for migration wizard."""

import logging

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from smk.core.config.manager import ConfigManager
from smk.core.exceptions import ConfigNotInitializedError

logger = logging.getLogger(__name__)
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


def _get_workflow_context(current_step: str, furthest_step: str | None = None) -> dict:
    """Build context data for workflow templates.

    Args:
        current_step: ID of current step
        furthest_step: ID of furthest step reached; determines completed_steps

    Returns:
        Dictionary with workflow context including stepper data and navigation
    """
    step_ids = [step["id"] for step in WORKFLOW_STEPS]
    current_index = step_ids.index(current_step)

    # Completed steps are derived from furthest_step, not current position
    furthest_index = max(
        current_index,
        step_ids.index(furthest_step) if furthest_step in step_ids else 0,
    )
    completed_steps = [step_ids[i] for i in range(furthest_index + 1) if step_ids[i] != current_step]

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


def _save_step(step: str) -> str:
    """Save the visited workflow step, advancing furthest_step if needed.

    Args:
        step: The step ID being visited.

    Returns:
        The furthest step reached (used to build stepper context).
    """
    try:
        manager = ConfigManager()
        state = manager.load_state()
        step_ids: list[str] = [str(s["id"]) for s in WORKFLOW_STEPS]
        current_idx = step_ids.index(step)
        furthest_idx = step_ids.index(state["furthest_step"]) if state["furthest_step"] in step_ids else 0
        furthest = step_ids[max(current_idx, furthest_idx)]
        manager.save_state(last_step=step, furthest_step=furthest)
        logger.info("Step visited: %s (furthest: %s)", step, furthest)
        return furthest
    except Exception:
        return step


@router.get("/", response_class=HTMLResponse, response_model=None)
async def workflow_root(request: Request) -> HTMLResponse | RedirectResponse:
    """Redirect to last visited step, or render start page."""
    last_step = ConfigManager().load_state()["last_step"]
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
    state = ConfigManager().load_state()
    context = _get_workflow_context("start", furthest_step=state["furthest_step"])
    context["request"] = request
    last_step = state["last_step"]
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
    furthest = _save_step("configure")
    templates = request.app.state.templates
    context = _get_workflow_context("configure", furthest_step=furthest)
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
    furthest = _save_step("export")
    templates = request.app.state.templates
    context = _get_workflow_context("export", furthest_step=furthest)
    context["request"] = request
    template = templates.get_template("pages/workflow/export.html")
    return HTMLResponse(template.render(**context))


@router.get("/audit", response_class=HTMLResponse)
async def workflow_audit(request: Request) -> HTMLResponse:
    """Render the workflow audit page."""
    furthest = _save_step("audit")
    templates = request.app.state.templates
    context = _get_workflow_context("audit", furthest_step=furthest)
    context["request"] = request
    template = templates.get_template("pages/workflow/audit.html")
    return HTMLResponse(template.render(**context))


@router.get("/migrate", response_class=HTMLResponse)
async def workflow_migrate(request: Request) -> HTMLResponse:
    """Render the workflow migrate page."""
    furthest = _save_step("migrate")
    templates = request.app.state.templates
    context = _get_workflow_context("migrate", furthest_step=furthest)
    context["request"] = request
    template = templates.get_template("pages/workflow/migrate.html")
    return HTMLResponse(template.render(**context))


@router.get("/cleanup", response_class=HTMLResponse)
async def workflow_cleanup(request: Request) -> HTMLResponse:
    """Render the workflow cleanup page."""
    furthest = _save_step("cleanup")
    templates = request.app.state.templates
    context = _get_workflow_context("cleanup", furthest_step=furthest)
    context["request"] = request
    template = templates.get_template("pages/workflow/cleanup.html")
    return HTMLResponse(template.render(**context))


@router.get("/complete", response_class=HTMLResponse)
async def workflow_complete(request: Request) -> HTMLResponse:
    """Render the workflow complete page."""
    furthest = _save_step("complete")
    templates = request.app.state.templates
    context = _get_workflow_context("complete", furthest_step=furthest)
    context["request"] = request
    template = templates.get_template("pages/workflow/complete.html")
    return HTMLResponse(template.render(**context))
