import click


@click.command(help="Delete temporary and migrated resources.")
@click.pass_context
def clean(ctx):
    console = ctx.obj["console"]

    console.print("This command has not been implemented yet.")
