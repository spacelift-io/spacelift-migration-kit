import sys
import click
from envyaml import EnvYAML
from exporters import get_exporter, TerraformExporter


class Context(object):
    def echo(self, *args, **kwargs):
        click.secho(*args, **kwargs)

    def error(self, message):
        click.secho(message, fg="red")

    def fail(self, message, exit_code=1):
        click.secho(message, fg="red")
        sys.exit(exit_code)

    def item(self, message, level=1, nl=False):
        padding = " " * (level - 1) * 2
        click.secho(f"{padding}- {message}: ", bold=True, nl=nl)

    def success(self, message="Success"):
        click.secho(message, fg="green")

class Generator(object):
    def __init__(self, ctx, settings):
        self.ctx = ctx
        self.settings = settings

    def generate(self):
        self.ctx.item("Generating Terraform code")
        self.ctx.success()

class Importer(object):
    def __init__(self, ctx, settings):
        self.ctx = ctx
        self.settings = settings

    def _create_manager_stack(self):
        self.ctx.item("Creating/updating manager stack", level=2)
        self.ctx.success()

    def _create_resources(self):
        self.ctx.item("Creating resources", level=2)
        self.ctx.success()

    def _upload_state_files(self):
        self.ctx.item("Uploading state files", level=2)
        self.ctx.success()

    def import_(self):
        self.ctx.item("Importing", nl=True)
        self._create_manager_stack()
        self._create_resources()
        self._upload_state_files()

def load_config(config_file):
    try:
        config = EnvYAML(config_file)
    except ValueError as e:
        raise click.BadParameter(e)

    return config


@click.group()
def cli():
    pass


@cli.command()
def config():
    click.echo("Generated configuration")


@cli.command()
@click.option(
    "-c",
    "--config",
    "config_file",
    default="config.yml",
    help="Path to configuration file.",
)
def migrate(config_file):
    ctx = Context()
    config = load_config(config_file)

    exporter = get_exporter(
        ctx=ctx,
        settings=config["exporter"],
    )
    exporter.export()

    generator = Generator(
        ctx=ctx,
        settings=config["generator"]
    )
    generator.generate()

    importer = Importer(
        ctx=ctx,
        settings=config["importer"]
    )
    importer.import_()

if __name__ == "__main__":
    cli()
