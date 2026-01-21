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
    def set_default(value, _default):
        return value if value is not None else _default

    generation_config = {
        "spacelift": {
            "manage_state": set_default(config.get("generator.spacelift.manage_state"), True)
        }, "github": {
            "custom_app": set_default(config.get("generator.github.custom_app"), False)
        },
        "custom_runner_image": set_default(config.get("generator.custom_runner_image"),
                                       "SPACELIFT_DEFAULT_INVALID"),
        "modules": {
            "default_branch": set_default(config.get("generator.modules.default_branch"), ""),
        },
        "stacks": {
            "default_branch": set_default(config.get("generator.stacks.default_branch"), ""),
        }
    }

    include_config = config.get("generator.include", {})

    generator = Generator()
    generator.generate(
        extra_vars=config.get("generator.extra_vars"),
        generation_config=generation_config,
        include_config=include_config
    )
