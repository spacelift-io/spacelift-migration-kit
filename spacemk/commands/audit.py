import click

from spacemk.exporters import load_exporter


@click.command(help="Audit the source vendor setup.")
@click.pass_context
def audit(ctx):
    config = ctx.obj["config"]
    exporter_name = config.get("exporter.name")
    exporter_settings = config.get("exporter.settings", {})
    exporter = load_exporter(console=ctx.obj["console"], name=exporter_name, settings=exporter_settings)
    exporter.audit()
