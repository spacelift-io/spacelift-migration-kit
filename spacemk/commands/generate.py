import click
from click_help_colors import HelpColorsCommand

from spacemk.generator import Generator


@click.command(
    cls=HelpColorsCommand,
    help="Generate Terraform code to manage Spacelift entities.",
    help_headers_color="yellow",
    help_options_color="green",
)
def generate():
    generator = Generator()
    generator.generate()
