import sys

from .terraform import TerraformExporter  # noqa: F401


def load_exporter(config, console):
    if not config.get("name"):
        raise ValueError("Exporter name is missing")

    class_name = f"{config.get('name').title()}Exporter"
    class_ = getattr(sys.modules[__name__], class_name)

    return class_(console=console, config=config.get("settings", {}))
