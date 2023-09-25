import click


@click.command(help="Export data from the source vendor.")
@click.pass_context
def export(ctx):
    console = ctx.obj["console"]

    console.print("This command has not been implemented yet.")
