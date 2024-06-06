import click
from click.decorators import pass_meta_key
from click_help_colors import HelpColorsCommand

from spacemk.generator import Generator


@click.command(
    cls=HelpColorsCommand,
    help="Generate Terraform code to manage Spacelift entities.",
    help_headers_color="yellow",
    help_options_color="green",
)
@pass_meta_key("config")
def generate(config):
    def default(value, default):
        return value if value is not None else default

    spacelift = default(config.get("generator.spacelift"), {"manage_state": True})
    github = default(config.get("generator.github"), {"custom_app": False})
    generation_config = {"spacelift": spacelift, "github": github}

    generator = Generator()
    generator.generate(extra_vars=config.get("generator.extra_vars"), generation_config=generation_config)
