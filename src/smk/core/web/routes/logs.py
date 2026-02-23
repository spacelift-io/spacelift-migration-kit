"""Logs page and SSE stream routes."""

import asyncio
import logging
from collections.abc import AsyncGenerator
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, StreamingResponse

logger = logging.getLogger(__name__)
router = APIRouter(tags=["logs"])


async def _log_stream(log_file: Path) -> AsyncGenerator[str, None]:
    offset = 0
    if log_file.exists():
        with log_file.open(encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    yield f"data: {line}\n\n"
            offset = f.tell()
    while True:
        await asyncio.sleep(0.5)
        if not log_file.exists():
            continue
        with log_file.open(encoding="utf-8") as f:
            f.seek(offset)
            chunk = f.read()
            offset = f.tell()
        for line in chunk.splitlines():
            line = line.strip()
            if line:
                yield f"data: {line}\n\n"


@router.get("/logs", response_class=HTMLResponse)
async def logs_page(request: Request) -> HTMLResponse:
    templates = request.app.state.templates
    template = templates.get_template("pages/logs.html")
    return HTMLResponse(template.render(request=request))


@router.get("/logs/stream")
async def logs_stream(request: Request) -> StreamingResponse:
    log_file: Path = request.app.state.log_file
    return StreamingResponse(
        _log_stream(log_file),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
