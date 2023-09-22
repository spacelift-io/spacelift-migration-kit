import click


@click.command(help="Create Spacelift entities.", name="import")
@click.pass_context
def import_(ctx):
    console = ctx.obj["console"]

    console.print("This command has not been implemented yet.")
