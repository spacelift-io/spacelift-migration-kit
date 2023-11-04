import click
from click.decorators import pass_meta_key

from spacemk.generator import Generator


@click.command(help="Generate Terraform code to manage Spacelift entities.")
@pass_meta_key("config")
def generate(config):
    generator = Generator(config.get("generator", {}))
    generator.generate()
