"""SMK Web interface."""

from smk.core.web.app import create_app
from smk.core.web.server import run_server

__all__ = ["create_app", "run_server"]
