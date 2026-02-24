"""Logs page and SSE stream routes."""

import asyncio
import logging
from collections import deque
from collections.abc import AsyncGenerator
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, StreamingResponse

logger = logging.getLogger(__name__)
router = APIRouter(tags=["logs"])

TAIL_LINES = 2000


async def _log_stream(log_file: Path, request: Request, *, live: bool = True) -> AsyncGenerator[str, None]:
    offset = 0
    if log_file.exists():
        with log_file.open(encoding="utf-8") as f:
            recent: deque[str] = deque(maxlen=TAIL_LINES)
            for line in f:
                line = line.strip()
                if line:
                    recent.append(line)
            offset = f.tell()
        for line in recent:
            yield f"data: {line}\n\n"
    if not live:
        return
    while not await request.is_disconnected():
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
async def logs_stream(request: Request, file: str | None = None) -> StreamingResponse:
    current_log: Path = request.app.state.log_file
    if file is not None:
        if Path(file).name != file:
            raise HTTPException(status_code=400, detail="Invalid file name")
        log_file = current_log.parent / file
        live = log_file == current_log
    else:
        log_file = current_log
        live = True
    return StreamingResponse(
        _log_stream(log_file, request, live=live),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
