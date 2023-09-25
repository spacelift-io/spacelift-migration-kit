import click


@click.command(help="Generate configuration file.")
@click.pass_context
def config(ctx):
    console = ctx.obj["console"]

    console.print("This command has not been implemented yet.")
    console.print(
        "For the time being, copy the [filename]config.yml.example[/filename] file to [filename]config.yml[/filename]"
        " and edit it."
    )
