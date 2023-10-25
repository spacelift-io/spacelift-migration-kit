import logging
import sys

import click
from benedict import benedict
from envyaml import EnvYAML
from rich.console import Console
from rich.logging import RichHandler
from rich.theme import Theme

from spacemk import commands


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
    ctx.obj["config"] = benedict(EnvYAML(config, flatten=False, include_environment=False))
    ctx.obj["console"] = console


custom_theme = Theme(
    {
        "error": "bold red",
        "path": "blue",
        "warning": "yellow",
    }
)
console = Console(theme=custom_theme)

spacemk.add_command(commands.audit)
spacemk.add_command(commands.clean)
spacemk.add_command(commands.config)
spacemk.add_command(commands.migrate)


def cli():
    try:
        spacemk()
    except KeyError as e:
        logging.critical(f"Unknown key: {e}")
        sys.exit(1)
    except Exception as e:
        logging.critical(e)
        sys.exit(1)


if __name__ == "__main__":
    cli()
