import logging
import sys
from pathlib import Path

import ccl
import click
from benedict import benedict
from click_help_colors import HelpColorsGroup, version_option
from dotenv import load_dotenv
from envyaml import EnvYAML
from icecream import ic
from rich.logging import RichHandler

from spacemk import __version__ as spacemk_version

ic.configureOutput(includeContext=True, contextAbsPath=True)
debug_enabled = False


@click.group(
    cls=HelpColorsGroup,
    help="Helper to move from various tools to Spacelift.",
    help_headers_color="yellow",
    help_options_color="green",
)
@version_option(prog_name="spacemk", prog_name_color="yellow", version=spacemk_version, version_color="green")
@click.option(
    "--config",
    default="config.yml",
    help="Path to the configuration file.",
    type=click.Path(),
)
@click.option("-v", "--verbose", "verbosity", count=True, default=1, help="Level of verbosity for the output.")
@click.pass_context
def spacemk(ctx, config, verbosity):
    load_dotenv()

    debug_verbosity = 2
    verbosity_to_level = [logging.WARNING, logging.INFO, logging.DEBUG]

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
                rich_tracebacks=True,
                show_path=debug_enabled,
                show_time=debug_enabled,
            )
        ],
        level=verbosity_to_level[verbosity],
    )

    ctx.meta["config"] = benedict(EnvYAML(config, flatten=False, include_environment=True))


current_file_path = Path(__file__).parent.resolve()

commands_folder = Path(f"{current_file_path}/commands").resolve()
ccl.register_commands(group=spacemk, source=commands_folder)

custom_commands_folder = Path(f"{current_file_path}/../custom/commands").resolve()
if custom_commands_folder.exists() and custom_commands_folder.is_dir():
    ccl.register_commands(group=spacemk, source=custom_commands_folder)


def app():
    try:
        spacemk()
    except Exception:
        logging.exception("The command failed")
        sys.exit(1)
