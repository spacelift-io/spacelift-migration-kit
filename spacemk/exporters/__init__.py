import logging
from importlib.machinery import SourceFileLoader
from pathlib import Path
from typing import Any

from spacemk.exporters.base import BaseExporter


def _get_exporter_class(exporter_name: str, path: Path) -> Any:
    class_name = f"{exporter_name.title()}Exporter"
    module = SourceFileLoader("exporters", path.as_posix()).load_module()

    if not hasattr(module, class_name):
        raise ValueError(f"Could not find '{class_name}' custom exporter class in '{path}'")

    class_ = getattr(module, class_name)

    if not issubclass(class_, BaseExporter):
        raise TypeError(f"'{class_name}' custom exporter class does not derive from the 'spacemk.BaseExporter' class")

    return class_


def load_exporter(config):
    exporter_name = config.get("name")

    if not exporter_name:
        raise ValueError("Exporter name is missing")

    current_file_path = Path(__file__).parent.resolve()

    custom_exporter_path = Path(current_file_path, f"../../custom/exporters/{exporter_name}.py").resolve()
    if custom_exporter_path.exists():
        logging.debug(f"Loading custom '{exporter_name}' exporter")
        class_ = _get_exporter_class(exporter_name=exporter_name, path=custom_exporter_path)
    else:
        logging.debug(f"Could not find custom '{exporter_name}' exporter. Looking for a native exporter.")

        native_exporter_path = Path(current_file_path, f"./{exporter_name}.py").resolve()
        if native_exporter_path.exists():
            logging.debug(f"Loading native '{exporter_name}' exporter")
            class_ = _get_exporter_class(exporter_name=exporter_name, path=native_exporter_path)
        else:
            raise FileNotFoundError(f"Could not find '{exporter_name}' exporter file")

    return class_(config=config.get("settings", {}))
