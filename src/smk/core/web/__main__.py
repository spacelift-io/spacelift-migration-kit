"""Web server entry point."""

from smk.core.web import run_server
from smk.core.web.config import WebConfig

if __name__ == "__main__":
    run_server(WebConfig())
