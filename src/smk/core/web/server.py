"""Web server lifecycle management."""

import threading
import time
import webbrowser
from typing import NoReturn

import uvicorn

from smk.core.web.app import create_app
from smk.core.web.config import WebConfig


def run_server(config: WebConfig) -> NoReturn:
    """Start the web server.

    Args:
        config: Web server configuration.
    """
    app = create_app(config)
    url = f"http://{config.host}:{config.port}"

    if config.open_browser:
        # Open browser after server starts
        def open_browser() -> None:
            time.sleep(1)
            webbrowser.open(url)

        threading.Thread(target=open_browser, daemon=True).start()

    uvicorn.run(
        app,
        host=config.host,
        port=config.port,
        log_level="debug" if config.debug else "info",
    )
    raise SystemExit(0)  # NoReturn requires this
