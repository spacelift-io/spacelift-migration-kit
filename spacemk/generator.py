import json
from pathlib import Path

from jinja2 import Environment, PackageLoader, select_autoescape


class Generator:
    def __init__(self, config, console):
        self._config = config
        self._console = console

    def _generate_code(self, data: dict):
        env = Environment(loader=PackageLoader("spacemk"), autoescape=select_autoescape())
        template = env.get_template("main.tf.jinja")
        content = template.render(**data)
        self._save_to_file("main.tf", content)

    def _load_data(self) -> dict:
        path = Path(f"{__file__}/../../tmp/data.json").resolve()

        with path.open("r") as fp:
            return json.load(fp)

    def _save_to_file(self, filename: str, content: str):
        folder = Path(f"{__file__}/../../tmp/code").resolve()
        if not Path.exists(folder):
            Path.mkdir(folder, parents=True)

        with Path(f"{folder}/{filename}").open("w") as fp:
            fp.write(content)

    def generate(self):
        """Generate source code for managing Spacelift entities"""
        data = self._load_data()
        self._generate_code(data)
