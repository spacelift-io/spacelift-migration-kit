import click

from spacemk.exporters import load_exporter


@click.command(help="Audit the source vendor setup.")
@click.pass_context
def audit(ctx):
    exporter = load_exporter(config=ctx.obj["config"].get("exporter", {}))
    exporter.audit()
