import click

from spacemk.exporters import load_exporter


@click.command(help="Export information from the source vendor.")
@click.pass_context
def export(ctx):
    config = ctx.obj["config"]

    exporter = load_exporter(config=config.get("exporter", {}), console=ctx.obj["console"])
    exporter.export()
