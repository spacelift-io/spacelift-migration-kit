import click


@click.command(help="Generate the source code to manage Spacelift entities.")
@click.pass_context
def generate(ctx):
    console = ctx.obj["console"]

    console.print("This command has not been implemented yet.")
