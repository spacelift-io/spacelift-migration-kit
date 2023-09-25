import click
from envyaml import EnvYAML
from rich.console import Console
from rich.theme import Theme

from . import commands


@click.group(help="Helper to move from various tools to Spacelift.")
@click.option(
    "--config",
    default="config.yml",
    help="Path to the configuration file.",
    type=click.Path(),
)
@click.pass_context
def cli(ctx, config):
    ctx.ensure_object(dict)

    ctx.obj["config"] = EnvYAML(config, strict=False)

    custom_theme = Theme(
        {
            "error": "bold red",
            "filename": "blue",
            "warning": "yellow",
        }
    )
    ctx.obj["console"] = Console(theme=custom_theme)


cli.add_command(commands.audit)
cli.add_command(commands.clean)
cli.add_command(commands.config)
cli.add_command(commands.migrate)


if __name__ == "__main__":
    cli()
