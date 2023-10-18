import sys

import click
from envyaml import EnvYAML
from rich.console import Console
from rich.theme import Theme

from spacemk import commands


@click.group(help="Helper to move from various tools to Spacelift.")
@click.option(
    "--config",
    default="config.yml",
    help="Path to the configuration file.",
    type=click.Path(),
)
@click.pass_context
def spacemk(ctx, config):
    ctx.ensure_object(dict)

    ctx.obj["config"] = EnvYAML(config, flatten=False, strict=True)

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
        console.print(f"[error]Unknown key: {e}[/error]")
    except Exception as e:
        console.print(f"[error]{e}[/error]")
        sys.exit(1)


if __name__ == "__main__":
    cli()
