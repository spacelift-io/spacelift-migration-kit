import click


@click.command(help="Migrate from the source vendor to Spacelift.")
@click.pass_context
def migrate(ctx):
    console = ctx.obj["console"]

    console.print("This command has not been implemented yet.")
