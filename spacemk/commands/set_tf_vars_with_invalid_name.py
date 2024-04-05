import click
from click.decorators import pass_meta_key
from click_help_colors import HelpColorsCommand

from spacemk.spacelift import Spacelift


@click.command(
    cls=HelpColorsCommand,
    help="Set value of Terraform variable with invalid name in Spacelift.",
    help_headers_color="yellow",
    help_options_color="green",
)
@pass_meta_key("config")
def set_tf_vars_with_invalid_name(config):
    spacelift = Spacelift(config.get("spacelift"))
    spacelift.set_terraform_vars_with_invalid_name()
