import click
import yaml


@click.command(help="Generate configuration file.")
@click.pass_context
def config(ctx):
    console = ctx.obj["console"]

    console.print("This command has not been implemented yet.")
    console.print(
        "For the time being, copy the [filename]config.yml.example[/filename] file to [filename]config.yml[/filename] and edit it."
    )

    # TODO: Ask questions to dynamically build this file
    # data = {
    #     "exporter": {}
    # }

    # with open(file, mode="wb") as f:
    #     yaml.safe_dump(data, f, encoding="utf-8", sort_keys=True)
