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

    async def _finite(log_file: Path, request: object):  # noqa: ARG001
        yield "data: {}\n\n"

    with patch("smk.core.web.routes.logs._log_stream", _finite), client.stream("GET", "/logs/stream") as response:
        assert response.status_code == 200
        assert "text/event-stream" in response.headers["content-type"]


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
