import click
from click.decorators import pass_meta_key

from spacemk.spacelift import Spacelift


@click.command(help="Set sensitive environment variable values in Spacelift.")
@pass_meta_key("config")
def set_sensitive_env_vars(config):
    spacelift = Spacelift(config.get("spacelift"))
    spacelift.set_sensitive_env_vars()
