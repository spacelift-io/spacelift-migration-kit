import click
from click.decorators import pass_meta_key
from click_help_colors import HelpColorsCommand

from spacemk.exporters import load_exporter


@click.command(
    cls=HelpColorsCommand,
    help="Export information from the source vendor.",
    help_headers_color="yellow",
    help_options_color="green",
)
@pass_meta_key("config")
def export(config):
    exporter = load_exporter(config=config.get("exporter", {}))
    exporter.export()
