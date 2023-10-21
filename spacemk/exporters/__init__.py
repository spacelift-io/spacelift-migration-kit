from importlib import import_module


def _import_class_from_string(path):
    module_path, _, class_name = path.rpartition(".")
    try:
        mod = import_module(module_path)
    except ModuleNotFoundError as e:
        raise ValueError("Exporter name is incorrect") from e

    return getattr(mod, class_name)


def load_exporter(config, console):
    if not config.get("name"):
        raise ValueError("Exporter name is missing")

    name = config.get("name")
    klass = _import_class_from_string(f"spacemk.exporters.{name}.Exporter")

    return klass(console=console, config=config.get("settings", {}))
