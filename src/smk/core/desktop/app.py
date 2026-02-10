"""Desktop application using pywebview wrapper."""

from __future__ import annotations

import multiprocessing
import threading

import uvicorn

from smk.core.web.app import create_app
from smk.core.web.config import WebConfig


def _start_server(port: int, config: WebConfig) -> None:
    """Start FastAPI server in background thread.

    Note: Reload mode is not supported in desktop mode because uvicorn's
    reload mechanism requires signal handlers that only work in the main thread.
    Use web-dev for development with auto-reload.

    Args:
        port: Port to bind the server to.
        config: Web server configuration.
    """
    app = create_app(config)
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=port,
        log_level="error",
    )


def _navigate(path: str, port: int) -> None:
    """Navigate to a path in the active webview window.

    Args:
        path: URL path to navigate to (e.g., "/", "/config").
        port: Port where the server is running.
    """
    import webview

    window = webview.active_window()
    if window:
        window.load_url(f"http://127.0.0.1:{port}{path}")


def launch_desktop(config: WebConfig | None = None) -> None:
    """Launch desktop application with pywebview wrapper.

    Starts FastAPI server in background thread and creates pywebview window.

    Args:
        config: Web server configuration. Uses defaults if None.
    """
    import webview
    from webview.menu import Menu, MenuAction, MenuSeparator

    multiprocessing.freeze_support()  # Needed for Windows

    if config is None:
        config = WebConfig()

    port = config.port

    # Start server in background thread
    threading.Thread(target=_start_server, args=(port, config), daemon=True).start()

    # Create menu
    menu = [
        Menu(
            "Navigate",
            [
                MenuAction("Dashboard", lambda: _navigate("/", port)),
                MenuSeparator(),
                MenuAction("Configuration", lambda: _navigate("/config", port)),
            ],
        ),
    ]

    # Create and start window
    webview.create_window(
        "SMK - Spacelift Migration Kit",
        f"http://127.0.0.1:{port}",
        width=1280,
        height=800,
    )
    webview.start(menu=menu)
