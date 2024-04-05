import click
from click.decorators import pass_meta_key
from click_help_colors import HelpColorsCommand

from spacemk.exporters import load_exporter


@click.command(
    cls=HelpColorsCommand,
    help="Audit the source vendor setup.",
    help_headers_color="yellow",
    help_options_color="green",
)
@pass_meta_key("config")
def audit(config):
    exporter = load_exporter(config=config.get("exporter", {}))
    exporter.audit()
