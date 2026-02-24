"""Tests for desktop application (desktop/app.py)."""

import importlib
from unittest.mock import MagicMock, patch

import smk.core.desktop.app as desktop_app
from smk.core.web.config import WebConfig


def _make_webview_mock() -> MagicMock:
    """Create a minimal webview module mock."""
    mock = MagicMock()
    mock.active_window.return_value = MagicMock()
    return mock


def _make_webview_menu_mock() -> MagicMock:
    mock = MagicMock()
    mock.Menu = MagicMock(return_value=MagicMock())
    mock.MenuAction = MagicMock(return_value=MagicMock())
    mock.MenuSeparator = MagicMock(return_value=MagicMock())
    return mock


def test_start_server_calls_uvicorn() -> None:
    """_start_server calls uvicorn.run with host=127.0.0.1 and log_level=error."""
    config = WebConfig(open_browser=False)
    with (
        patch("smk.core.desktop.app.create_app") as mock_create,
        patch("smk.core.desktop.app.uvicorn.run") as mock_run,
    ):
        desktop_app._start_server(8080, config)

    mock_create.assert_called_once_with(config)
    mock_run.assert_called_once_with(
        mock_create.return_value,
        host="127.0.0.1",
        port=8080,
        log_level="error",
    )


def test_navigate_calls_load_url() -> None:
    """_navigate calls load_url on the active window."""
    webview_mock = _make_webview_mock()

    with patch.dict("sys.modules", {"webview": webview_mock}):
        importlib.reload(desktop_app)
        desktop_app._navigate("/dashboard", 8765)

    webview_mock.active_window.return_value.load_url.assert_called_once_with("http://127.0.0.1:8765/dashboard")


def test_navigate_no_op_when_no_active_window() -> None:
    """_navigate does nothing when webview.active_window() returns None."""
    webview_mock = _make_webview_mock()
    webview_mock.active_window.return_value = None

    with patch.dict("sys.modules", {"webview": webview_mock}):
        importlib.reload(desktop_app)
        # Should not raise
        desktop_app._navigate("/", 8765)


def test_launch_desktop_with_none_config_uses_defaults() -> None:
    """launch_desktop creates WebConfig() when config=None."""
    webview_mock = _make_webview_mock()
    webview_menu_mock = _make_webview_menu_mock()

    with (
        patch.dict("sys.modules", {"webview": webview_mock, "webview.menu": webview_menu_mock}),
        patch("smk.core.desktop.app.create_app"),
        patch("smk.core.desktop.app.uvicorn.run"),
        patch("smk.core.desktop.app.threading.Thread") as mock_thread,
        patch("smk.core.desktop.app.multiprocessing.freeze_support"),
    ):
        importlib.reload(desktop_app)
        desktop_app.launch_desktop(None)

    # The config passed to _start_server (via thread args) should be WebConfig default
    call_args = mock_thread.call_args
    _, config = call_args.kwargs["args"]
    assert config == WebConfig()


def test_launch_desktop_creates_window_and_starts() -> None:
    """launch_desktop calls webview.create_window and webview.start."""
    webview_mock = _make_webview_mock()
    webview_menu_mock = _make_webview_menu_mock()

    config = WebConfig(port=9999, open_browser=False)

    with (
        patch.dict("sys.modules", {"webview": webview_mock, "webview.menu": webview_menu_mock}),
        patch("smk.core.desktop.app.create_app"),
        patch("smk.core.desktop.app.uvicorn.run"),
        patch("smk.core.desktop.app.threading.Thread"),
        patch("smk.core.desktop.app.multiprocessing.freeze_support"),
    ):
        importlib.reload(desktop_app)
        desktop_app.launch_desktop(config)

    webview_mock.create_window.assert_called_once()
    webview_mock.start.assert_called_once()
