import json
from pathlib import Path

from jinja2 import Environment, PackageLoader, nodes
from jinja2.exceptions import TemplateRuntimeError
from jinja2.ext import Extension


class RaiseExtension(Extension):
    tags = set(["raise"])  # noqa: RUF012

    def parse(self, parser):
        lineno = next(parser.stream).lineno
        message_node = parser.parse_expression()

        return nodes.CallBlock(self.call_method("_raise", [message_node], lineno=lineno), [], [], [], lineno=lineno)

    def _raise(self, msg, caller):  # noqa: ARG002
        raise TemplateRuntimeError(msg)


class Generator:
    def __init__(self, config, console):
        self._config = config
        self._console = console

    def _filter_totf(self, value):
        return json.dumps(value, ensure_ascii=False)

    def _generate_code(self, data: dict):
        env = Environment(
            autoescape=False,
            extensions=[RaiseExtension],
            loader=PackageLoader("spacemk"),
            lstrip_blocks=True,
            trim_blocks=True,
        )
        env.filters["totf"] = self._filter_totf
        template = env.get_template("main.tf.jinja")
        content = template.render(**data)
        self._save_to_file("main.tf", content)

    def _load_data(self) -> dict:
        path = Path(f"{__file__}/../../tmp/data.json").resolve()

        with path.open("r", encoding="utf-8") as fp:
            return json.load(fp)

    def _save_to_file(self, filename: str, content: str):
        folder = Path(f"{__file__}/../../tmp/code").resolve()
        if not Path.exists(folder):
            Path.mkdir(folder, parents=True)

        with Path(f"{folder}/{filename}").open("w", encoding="utf-8") as fp:
            fp.write(content)

    def generate(self):
        """Generate source code for managing Spacelift entities"""
        data = self._load_data()
        self._generate_code(data)
