import click
from click.decorators import pass_meta_key

from spacemk.exporters import load_exporter


@click.command(help="Export information from the source vendor.")
@pass_meta_key("config")
def export(config):
    exporter = load_exporter(config=config.get("exporter", {}))
    exporter.export()
