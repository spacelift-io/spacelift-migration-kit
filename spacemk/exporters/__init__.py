from importlib import import_module


def _import_class_from_string(path):
    module_path, _, class_name = path.rpartition(".")
    mod = import_module(module_path)

    return getattr(mod, class_name)


def load_exporter(config, console):
    name = config.get("name")
    settings = config.get("settings", {})

    klass = _import_class_from_string(f"spacemk.exporters.{name}.Exporter")

    return klass(console, **settings)
