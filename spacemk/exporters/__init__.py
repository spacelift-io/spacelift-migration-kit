from importlib import import_module


def _import_class_from_string(path):
    module_path, _, class_name = path.rpartition(".")
    mod = import_module(module_path)
    klass = getattr(mod, class_name)

    return klass


def load_exporter(console, name, settings=None):
    if settings is None:
        settings = {}

    klass = _import_class_from_string(f"spacemk.exporters.{name}.Exporter")
    return klass(console, **settings)
