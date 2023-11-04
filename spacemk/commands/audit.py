import click
from click.decorators import pass_meta_key

from spacemk.exporters import load_exporter


@click.command(help="Audit the source vendor setup.")
@pass_meta_key("config")
def audit(config):
    exporter = load_exporter(config=config.get("exporter", {}))
    exporter.audit()
