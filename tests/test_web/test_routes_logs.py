"""Tests for logs page and SSE stream routes."""

import json
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient


def test_logs_page_returns_200(client: TestClient) -> None:
    """Logs page returns 200 OK."""
    response = client.get("/logs")
    assert response.status_code == 200


def test_logs_page_contains_log_viewer(client: TestClient) -> None:
    """Logs page includes the Alpine.js logViewer component."""
    response = client.get("/logs")
    assert "logViewer" in response.text


def test_logs_stream_content_type(client: TestClient) -> None:
    """SSE stream returns text/event-stream content type."""

    async def _finite(log_file: Path, request: object, *, live: bool = True):  # noqa: ARG001
        yield "data: {}\n\n"

    with patch("smk.core.web.routes.logs._log_stream", _finite), client.stream("GET", "/logs/stream") as response:
        assert response.status_code == 200
        assert "text/event-stream" in response.headers["content-type"]


@pytest.mark.asyncio
async def test_logs_stream_tail_limits_initial_lines(tmp_path: Path) -> None:
    """_log_stream yields at most TAIL_LINES entries on initial connect."""
    from unittest.mock import AsyncMock

    from smk.core.web.routes.logs import TAIL_LINES, _log_stream

    log_file = tmp_path / "big.log"
    n = TAIL_LINES + 50
    lines = [json.dumps({"time": "T", "level": "INFO", "logger": "smk", "message": f"line {i}"}) for i in range(n)]
    log_file.write_text("\n".join(lines) + "\n")

    mock_request = AsyncMock()
    mock_request.is_disconnected.return_value = True

    events = [e async for e in _log_stream(log_file, mock_request, live=False)]

    assert len(events) == TAIL_LINES
    assert json.loads(events[-1][6:].strip())["message"] == f"line {n - 1}"
    assert json.loads(events[0][6:].strip())["message"] == f"line {50}"


@pytest.mark.asyncio
async def test_logs_stream_replays_existing_entries(tmp_path: Path) -> None:
    """_log_stream replays existing log file entries on connect."""
    from smk.core.web.routes.logs import _log_stream

    log_file = tmp_path / "test.log"
    entry = {"time": "T", "level": "INFO", "logger": "smk.test", "message": "hello"}
    log_file.write_text(json.dumps(entry) + "\n")

    from unittest.mock import AsyncMock

    mock_request = AsyncMock()
    mock_request.is_disconnected.return_value = False

    gen = _log_stream(log_file, mock_request)
    try:
        event = await gen.__anext__()
    finally:
        await gen.aclose()

    assert event.startswith("data: ")
    parsed = json.loads(event[6:].strip())
    assert parsed["message"] == "hello"


def test_list_log_files_returns_list(client: TestClient, tmp_path: Path) -> None:
    """GET /api/logs returns list of log files with correct current flags."""
    current = tmp_path / "smk-2026-02-23T120000.log"
    older = tmp_path / "smk-2026-02-22T080000.log"
    current.write_text("")
    older.write_text("")

    client.app.state.log_file = current  # type: ignore[attr-defined]

    response = client.get("/api/logs")
    assert response.status_code == 200

    files = response.json()
    assert isinstance(files, list)
    assert len(files) == 2

    by_name = {f["name"]: f for f in files}
    assert by_name[current.name]["current"] is True
    assert by_name[older.name]["current"] is False


def test_logs_stream_rejects_traversal(client: TestClient) -> None:
    """GET /logs/stream?file=../etc/passwd returns 400."""
    response = client.get("/logs/stream?file=../etc/passwd")
    assert response.status_code == 400
