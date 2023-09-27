import click


@click.command(help="Generate configuration file.")
@click.pass_context
def config(ctx):
    console = ctx.obj["console"]

    console.print("This command has not been implemented yet.")
    console.print(
        "For the time being, copy the [path]config.yml.example[/path] file to [path]config.yml[/path]" " and edit it."
    )
