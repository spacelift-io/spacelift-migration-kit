import click

from spacemk.code_publisher import CodePublisher
from spacemk.exporters import load_exporter
from spacemk.generator import Generator
from spacemk.importer import Importer
from spacemk.state_uploader import StateUploader


@click.command(help="Migrate from the source vendor to Spacelift.")
@click.pass_context
def migrate(ctx):
    # Export data from the source vendor
    exporter = load_exporter(config=ctx.obj["config"].get("exporter", {}), console=ctx.obj["console"])
    exporter.export()

    # Generate the source code to manage Spacelift entities
    generator = Generator(config=ctx.obj["config"].get("generator", {}), console=ctx.obj["console"])
    generator.generate()

    # Push the generated source code to a git repository
    code_publisher = CodePublisher(config=ctx.obj["config"].get("code_publisher", {}), console=ctx.obj["console"])
    code_publisher.publish()

    # Create the Spacelift manager stack and trigger a run to create the entities
    importer = Importer(config=ctx.obj["config"].get("importer", {}), console=ctx.obj["console"])
    importer.create()

    # Upload Terraform state files to the state backend
    state_uploader = StateUploader(config=ctx.obj["config"].get("state_uploader", {}), console=ctx.obj["console"])
    state_uploader.upload_state_files()
