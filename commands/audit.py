import click

from importlib import import_module


def _import_class_from_string(path):
    module_path, _, class_name = path.rpartition(".")
    mod = import_module(module_path)
    klass = getattr(mod, class_name)

    return klass


def _load_exporter(console, name, settings={}):
    klass = _import_class_from_string(f"exporters.{name}.Exporter")
    return klass(console, **settings)


@click.command(help="Audit the source vendor setup.")
@click.pass_context
def audit(ctx):
    config = ctx.obj["config"]
    exporter_settings = config["exporter"]
    exporter_name = exporter_settings.pop("name")
    exporter = _load_exporter(
        console=ctx.obj["console"], name=exporter_name, settings=exporter_settings
    )
    exporter.audit()
