import click

from spacemk.generator import Generator


@click.command(help="Generate Terraform code to manage Spacelift entities.")
@click.pass_context
def generate(ctx):
    config = ctx.obj["config"]

    generator = Generator(config=config.get("generator", {}), console=ctx.obj["console"])
    generator.generate()
