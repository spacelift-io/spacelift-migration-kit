"""Tests for web server lifecycle."""

import contextlib
import threading
from unittest.mock import MagicMock, patch

from smk.core.web.config import WebConfig
from smk.core.web.server import run_server


def test_run_server_no_browser_no_reload() -> None:
    """run_server calls uvicorn.run with app instance when reload disabled."""
    config = WebConfig(open_browser=False, reload=False, debug=False)
    mock_app = MagicMock()

    with (
        patch("smk.core.web.server.create_app", return_value=mock_app) as mock_create,
        patch("smk.core.web.server.uvicorn.run") as mock_run,
        contextlib.suppress(SystemExit),
    ):
        run_server(config)

    mock_create.assert_called_once_with(config)
    mock_run.assert_called_once_with(
        mock_app,
        host=config.host,
        port=config.port,
        log_level="info",
    )


def test_run_server_with_reload() -> None:
    """run_server passes factory import string to uvicorn when reload enabled."""
    config = WebConfig(open_browser=False, reload=True, debug=False)

    with (
        patch("smk.core.web.server.create_app") as mock_create,
        patch("smk.core.web.server.uvicorn.run") as mock_run,
        contextlib.suppress(SystemExit),
    ):
        run_server(config)

    # create_app should NOT be called directly in reload mode
    mock_create.assert_not_called()
    call_kwargs = mock_run.call_args
    assert call_kwargs.args[0] == "smk.core.web.app:create_app"
    assert call_kwargs.kwargs["factory"] is True
    assert call_kwargs.kwargs["reload"] is True


def test_run_server_opens_browser() -> None:
    """run_server starts browser thread when open_browser is True."""
    config = WebConfig(open_browser=True, reload=False)
    started_threads: list[threading.Thread] = []

    def capture_start(self: threading.Thread) -> None:
        started_threads.append(self)

    with (
        patch("smk.core.web.server.create_app"),
        patch("smk.core.web.server.uvicorn.run"),
        patch.object(threading.Thread, "start", capture_start),
        contextlib.suppress(SystemExit),
    ):
        run_server(config)

    assert len(started_threads) == 1
