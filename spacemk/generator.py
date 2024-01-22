import json
import logging
import os
import subprocess
from pathlib import Path

import click
from jinja2 import ChoiceLoader, Environment, FileSystemLoader, nodes
from jinja2.exceptions import TemplateNotFound, TemplateRuntimeError
from jinja2.ext import Extension

from spacemk import get_tmp_subfolder, is_command_available, load_normalized_data


class RaiseExtension(Extension):
    tags = set(["raise"])  # noqa: RUF012

    def parse(self, parser):
        lineno = next(parser.stream).lineno
        message_node = parser.parse_expression()

        return nodes.CallBlock(self.call_method("_raise", [message_node], lineno=lineno), [], [], [], lineno=lineno)

    def _raise(self, msg, caller):  # noqa: ARG002
        raise TemplateRuntimeError(msg)


class Generator:
    def _check_requirements(self) -> None:
        """Check if the exporter requirements are met"""
        logging.info("Start checking requirements")

        if not is_command_available("terraform"):
            logging.warning("Terraform is not available. Generated source code will not be formatted or validated.")

            click.confirm("Do you want to continue?", abort=True)

        logging.info("Stop checking requirements")

    def _filter_normalizepath(self, value: str) -> str:
        return os.path.normpath(value)

    def _filter_randomsuffix(self, value: str) -> str:
        return f"{value}_{os.urandom(8).hex()}"

    def _filter_totf(self, value: any) -> str:
        return json.dumps(value, ensure_ascii=False)

    def _format_code(self) -> None:
        if not is_command_available("terraform"):
            logging.warning("Terraform is not installed. Skipping generated Terraform code formatting.")
            return

        folder_path = get_tmp_subfolder("code")
        process = subprocess.run(
            f"terraform fmt -no-color {folder_path}", capture_output=True, check=False, shell=True, text=True
        )

        if process.returncode != 0:
            logging.warning(f"Could not format generated Terraform code: {process.stderr}")
        else:
            logging.info("Formatted generated Terraform code")

    def _generate_code(self, data: dict, template_name: str):
        current_file_path = Path(__file__).parent.resolve()

        env = Environment(
            autoescape=False,
            extensions=[RaiseExtension],
            loader=ChoiceLoader(
                [
                    FileSystemLoader(Path(f"{current_file_path}/../custom/templates").resolve()),
                    FileSystemLoader(Path(f"{current_file_path}/templates").resolve()),
                ]
            ),
            lstrip_blocks=True,
            trim_blocks=True,
        )
        env.filters["normalizepath"] = self._filter_normalizepath
        env.filters["randomsuffix"] = self._filter_randomsuffix
        env.filters["totf"] = self._filter_totf

        try:
            content = env.get_template(name=template_name, parent="base.tf.jinja").render(**data)
        except TemplateNotFound as e:
            raise FileNotFoundError(f"Template not found '{e.message}'") from e

        self._save_to_file("main.tf", content)

    def _load_data(self) -> dict:
        return load_normalized_data()

    def _process_data(self, data: dict) -> dict:
        logging.info("No custom data processing defined. Skipping.")
        return data

    def _save_to_file(self, filename: str, content: str):
        path = Path(get_tmp_subfolder("code"), filename)

        with path.open("w", encoding="utf-8") as fp:
            fp.write(content)

    def _validate_code(self) -> None:
        if not is_command_available("terraform"):
            logging.warning("Terraform is not installed. Skipping generated Terraform code validation.")
            return

        path = get_tmp_subfolder("code")
        process = subprocess.run(
            f"terraform -chdir={path} init -backend=false -no-color && terraform -chdir={path} validate -no-color",
            capture_output=True,
            check=False,
            shell=True,
            text=True,
        )

        if process.returncode != 0:
            logging.warning(f"Generated Terraform code is invalid: {process.stderr}")
        else:
            logging.info("Generated Terraform code is valid")

    def generate(self, template_name: str = "main.tf.jinja"):
        """Generate source code for managing Spacelift entities"""
        self._check_requirements()
        data = self._load_data()
        data = self._process_data(data)
        self._generate_code(data=data, template_name=template_name)
        self._format_code()
        self._validate_code()
