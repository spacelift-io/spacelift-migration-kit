"""
SMK CLI application.

Commands follow the pattern: smk <subject> <action>
where subject is a noun and action is a verb.
"""

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as get_version

import typer

app = typer.Typer(
    help="Spacelift Migration Kit - Migrate infrastructure management to Spacelift",
    name="smk",
    no_args_is_help=True,
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


@app.callback()
def main_callback(
    version: bool = typer.Option(
        False,
        "--version",
        callback=version_callback,
        help="Show SMK version and exit.",
        is_eager=True,
    ),
) -> None:
    """Spacelift Migration Kit - Migrate infrastructure management to Spacelift."""
