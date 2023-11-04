import logging
import sys
from pathlib import Path

import ccl
import click
from benedict import benedict
from envyaml import EnvYAML
from rich.console import Console
from rich.logging import RichHandler
from rich.theme import Theme

debug_enabled = False


@click.group(help="Helper to move from various tools to Spacelift.")
@click.option(
    "--config",
    default="config.yml",
    help="Path to the configuration file.",
    type=click.Path(),
)
@click.option("-v", "--verbose", "verbosity", count=True, default=0, help="Level of verbosity for the output.")
@click.pass_context
def spacemk(ctx, config, verbosity):
    debug_verbosity = 3
    verbosity_to_level = [logging.ERROR, logging.WARNING, logging.INFO, logging.DEBUG]

    if verbosity > debug_verbosity:
        verbosity = debug_verbosity

    global debug_enabled  # noqa: PLW0603
    debug_enabled = verbosity == debug_verbosity

    logging.basicConfig(
        datefmt="[%X]",
        format="%(message)s",
        handlers=[
            RichHandler(
                omit_repeated_times=False,
                rich_tracebacks=debug_enabled,
                show_path=debug_enabled,
                show_time=debug_enabled,
            )
        ],
        level=verbosity_to_level[verbosity],
    )

    ctx.ensure_object(dict)
    ctx.obj["config"] = benedict(EnvYAML(config, flatten=False, include_environment=True))
    ctx.obj["console"] = console


custom_theme = Theme(
    {
        "error": "bold red",
        "path": "blue",
        "warning": "yellow",
    }
)
console = Console(theme=custom_theme)

commands_folder = Path(f"{Path(__file__).parent.resolve()}/commands").resolve()
ccl.register_commands(group=spacemk, source=commands_folder)

custom_commands_folder = Path(f"{__file__}/../../custom/commands").resolve()
if custom_commands_folder.exists() and custom_commands_folder.is_dir():
    ccl.register_commands(group=spacemk, source=custom_commands_folder)


def cli():
    try:
        spacemk()
    except KeyError as e:
        logging.critical(f"Unknown key: {e}", exc_info=debug_enabled)
        sys.exit(1)
    except Exception as e:
        logging.critical(e, exc_info=debug_enabled)
        sys.exit(1)


if __name__ == "__main__":
    cli()
