"""SMK CLI application."""

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as get_version

import typer

from smk.core.web import run_server
from smk.core.web.config import WebConfig

app = typer.Typer(
    help="Spacelift Migration Kit - Migrate infrastructure management to Spacelift",
    name="smk",
)


def version_callback(value: bool) -> None:
    """Show SMK version and exit."""
    if value:
        try:
            version = get_version("smk")
        except PackageNotFoundError:
            version = "unknown"
        typer.echo(f"SMK version {version}")
        raise typer.Exit()


@app.callback(invoke_without_command=True)
def main_callback(
    ctx: typer.Context,
    _version: bool = typer.Option(
        False,
        "--version",
        callback=version_callback,
        help="Show SMK version and exit.",
        is_eager=True,
    ),
) -> None:
    """Launch SMK web interface."""
    if ctx.invoked_subcommand is None:
        run_server(WebConfig())
