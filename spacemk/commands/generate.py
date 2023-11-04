import click

from spacemk.generator import Generator


@click.command(help="Generate Terraform code to manage Spacelift entities.")
def generate():
    generator = Generator()
    generator.generate()
