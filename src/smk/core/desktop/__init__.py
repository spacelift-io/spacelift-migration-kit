"""Desktop application module."""

from smk.core.desktop.app import launch_desktop
from smk.core.desktop.launcher import is_desktop_available

__all__ = ["is_desktop_available", "launch_desktop"]
