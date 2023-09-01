from .base import BaseExporter
from .terraform import TerraformExporter

import pprint

def get_exporter(ctx, settings):
    name = settings["name"]
    if name in ["tfc", "tfe"]:
        exporter = TerraformExporter(ctx=ctx, flavor=name, settings=settings)
    else:
        ctx.fail(f"Invalid exporter name: {name}")

    return exporter
