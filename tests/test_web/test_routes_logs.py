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


@pytest.mark.asyncio
async def test_log_stream_skips_empty_lines(tmp_path: Path) -> None:
    """_log_stream skips empty lines in the log file (covers 25->23 branch)."""
    from unittest.mock import AsyncMock

    from smk.core.web.routes.logs import _log_stream

    log_file = tmp_path / "test.log"
    log_file.write_text('{"msg": "a"}\n\n{"msg": "b"}\n')

    mock_request = AsyncMock()
    mock_request.is_disconnected.return_value = True

    events = [e async for e in _log_stream(log_file, mock_request, live=False)]
    assert len(events) == 2


@pytest.mark.asyncio
async def test_log_stream_live_polls_for_new_content(tmp_path: Path) -> None:
    """_log_stream live mode polls and yields new lines after initial replay."""
    from unittest.mock import AsyncMock

    from smk.core.web.routes.logs import _log_stream

    log_file = tmp_path / "live.log"
    log_file.write_text("")

    call_count = 0

    async def is_disconnected() -> bool:
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            # First call: not disconnected, write new content including an empty line
            log_file.write_text('{"msg": "new"}\n\n')
            return False
        return True  # Second call: disconnect

    mock_request = AsyncMock()
    mock_request.is_disconnected.side_effect = is_disconnected

    with patch("smk.core.web.routes.logs.asyncio.sleep"):
        events = [e async for e in _log_stream(log_file, mock_request, live=True)]

    assert len(events) == 1
    assert '"new"' in events[0]


def test_logs_stream_valid_file_param_sets_live(client: TestClient, tmp_path: Path) -> None:
    """GET /logs/stream?file=<current-log-name> sets live=True (lines 59-60)."""
    from unittest.mock import patch

    current = tmp_path / "smk-current.log"
    current.write_text("")
    client.app.state.log_file = current  # type: ignore[attr-defined]

    async def _finite(log_file: Path, request: object, *, live: bool = True):  # noqa: ARG001
        yield "data: {}\n\n"

    with (
        patch("smk.core.web.routes.logs._log_stream", _finite),
        client.stream("GET", f"/logs/stream?file={current.name}") as response,
    ):
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_log_stream_live_skips_nonexistent_file(tmp_path: Path) -> None:
    """_log_stream live polling continues when log file doesn't exist yet (line 34-35)."""
    from unittest.mock import AsyncMock

    from smk.core.web.routes.logs import _log_stream

    log_file = tmp_path / "not_yet.log"
    call_count = 0

    async def is_disconnected() -> bool:
        nonlocal call_count
        call_count += 1
        return call_count != 1  # First poll: not disconnected; subsequent: disconnected

    mock_request = AsyncMock()
    mock_request.is_disconnected.side_effect = is_disconnected

    with patch("smk.core.web.routes.logs.asyncio.sleep"):
        events = [e async for e in _log_stream(log_file, mock_request, live=True)]

    assert events == []


@pytest.mark.asyncio
async def test_log_stream_missing_file_no_events(tmp_path: Path) -> None:
    """_log_stream yields no events when the log file does not exist."""
    from unittest.mock import AsyncMock

    from smk.core.web.routes.logs import _log_stream

    missing = tmp_path / "does_not_exist.log"
    mock_request = AsyncMock()
    mock_request.is_disconnected.return_value = True

    events = [e async for e in _log_stream(missing, mock_request, live=False)]
    assert events == []


def test_logs_stream_rejects_traversal(client: TestClient) -> None:
    """GET /logs/stream?file=../etc/passwd returns 400."""
    response = client.get("/logs/stream?file=../etc/passwd")
    assert response.status_code == 400
