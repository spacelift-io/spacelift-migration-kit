"""Main TUI application for SMK."""

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as get_version
from typing import ClassVar

from textual.app import App, ComposeResult
from textual.binding import Binding, BindingType
from textual.containers import Center, Middle
from textual.widgets import Footer, Header, Static


def _get_version() -> str:
    """Get SMK version."""
    try:
        return get_version("smk")
    except PackageNotFoundError:
        return "unknown"


class WelcomeMessage(Static):
    """Welcome message widget."""

    DEFAULT_CSS = """
    WelcomeMessage {
        width: auto;
        height: auto;
        padding: 2 4;
        border: solid $primary;
        background: $surface;
        text-align: center;
    }
    """

    def __init__(self) -> None:
        """Initialize welcome message."""
        version = _get_version()
        message = f"Welcome to SMK v{version}\n\nSpacelift Migration Kit"
        super().__init__(message)


class TUIApp(App[None]):
    """SMK TUI application."""

    TITLE = "SMK - Spacelift Migration Kit"

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("q", "quit", "Quit"),
        Binding("question_mark", "help", "Help"),
    ]

    DEFAULT_CSS = """
    Screen {
        align: center middle;
    }
    """

    def compose(self) -> ComposeResult:
        """Compose the TUI layout."""
        yield Header()
        yield Middle(Center(WelcomeMessage()))
        yield Footer()

    def action_help(self) -> None:
        """Show help (placeholder)."""
        self.notify("Help coming soon!")
