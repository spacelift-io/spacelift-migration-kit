"""
SMK CLI application.

Commands follow the pattern: smk <subject> <action>
where subject is a noun and action is a verb.
"""

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as get_version
from pathlib import Path
from typing import Annotated

import typer

from smk.core.config.manager import ConfigManager

app = typer.Typer(
    help="Spacelift Migration Kit - Migrate infrastructure management to Spacelift",
    name="smk",
)

config_app = typer.Typer(help="Configuration management commands")
app.add_typer(config_app, name="config")


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
    """Spacelift Migration Kit - Migrate infrastructure management to Spacelift."""
    if ctx.invoked_subcommand is None:
        from smk.core.tui import TUIApp

        TUIApp().run()


@config_app.command("init")
def config_init(
    config_dir: Annotated[
        Path | None,
        typer.Option(
            "--config-dir",
            "-c",
            help="Custom configuration directory. Defaults to $XDG_CONFIG_HOME/smk.",
        ),
    ] = None,
    force: Annotated[
        bool,
        typer.Option(
            "--force",
            "-f",
            help="Overwrite existing configuration.",
        ),
    ] = False,
    source_plugin: Annotated[
        str | None,
        typer.Option(
            "--source",
            "-s",
            help="Source vendor plugin (e.g., terraform-cloud, terraform-enterprise).",
        ),
    ] = None,
    spacelift_endpoint: Annotated[
        str | None,
        typer.Option(
            "--spacelift-endpoint",
            help="Spacelift API endpoint (e.g., https://example.app.spacelift.io).",
        ),
    ] = None,
    spacelift_key_id: Annotated[
        str | None,
        typer.Option(
            "--spacelift-key-id",
            help="Spacelift API key ID.",
        ),
    ] = None,
    spacelift_key_secret: Annotated[
        str | None,
        typer.Option(
            "--spacelift-key-secret",
            help="Spacelift API key secret.",
        ),
    ] = None,
) -> None:
    """Initialize SMK configuration.

    Creates the configuration directory structure and config file.
    Prompts for any missing values interactively.
    """
    manager = ConfigManager(config_dir)

    # Interactive prompts for missing values
    if source_plugin is None:
        source_plugin = typer.prompt("Source vendor plugin", default="") or None

    if spacelift_endpoint is None:
        spacelift_endpoint = typer.prompt("Spacelift API endpoint", default="") or None

    if spacelift_key_id is None:
        spacelift_key_id = typer.prompt("Spacelift API key ID", default="") or None

    if spacelift_key_secret is None:
        spacelift_key_secret = typer.prompt("Spacelift API key secret", default="", hide_input=True) or None

    # Convert empty strings to None
    source_plugin = source_plugin or None
    spacelift_endpoint = spacelift_endpoint or None
    spacelift_key_id = spacelift_key_id or None
    spacelift_key_secret = spacelift_key_secret or None

    try:
        manager.init(
            force=force,
            source_plugin=source_plugin,
            spacelift_endpoint=spacelift_endpoint,
            spacelift_key_id=spacelift_key_id,
            spacelift_key_secret=spacelift_key_secret,
        )
        typer.echo(f"Configuration initialized at {manager.config_file}")
    except FileExistsError as e:
        typer.echo(str(e), err=True)
        raise typer.Exit(code=1) from None


@config_app.command("show")
def config_show(
    config_dir: Annotated[
        Path | None,
        typer.Option(
            "--config-dir",
            "-c",
            help="Custom configuration directory.",
        ),
    ] = None,
) -> None:
    """Show current configuration."""
    from smk.core.exceptions import ConfigNotInitializedError

    manager = ConfigManager(config_dir)

    try:
        config = manager.load()
    except ConfigNotInitializedError as e:
        typer.echo(str(e), err=True)
        raise typer.Exit(code=1) from None

    typer.echo(f"Config file: {manager.config_file}")
    typer.echo(f"Config version: {config.config_version}")
    typer.echo(f"Source plugin: {config.source.plugin or '(not set)'}")
    typer.echo(f"Spacelift endpoint: {config.spacelift.api_endpoint or '(not set)'}")
    typer.echo(f"Spacelift key ID: {config.spacelift.api_key_id or '(not set)'}")
    typer.echo(f"Spacelift key secret: {'***' if config.spacelift.api_key_secret else '(not set)'}")
