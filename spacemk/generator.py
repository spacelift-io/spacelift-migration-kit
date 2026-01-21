import json
import logging
import os
import re
import subprocess
from pathlib import Path
from typing import Optional

import click
from jinja2 import ChoiceLoader, Environment, FileSystemLoader, StrictUndefined, nodes
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

    def _generate_code(self, data: dict, extra_vars: dict, template_name: str, generation_config: dict):
        data["extra_vars"] = extra_vars
        data["generation_config"] = generation_config

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
            undefined=StrictUndefined,
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

    def _filter_stacks(self, data: dict, pattern_str: str) -> set:
        """Filter stacks by name pattern and return set of included stack IDs."""
        pattern = re.compile(pattern_str)
        original_count = len(data.get("stacks", []))
        data["stacks"] = [s for s in data.get("stacks", []) if pattern.match(s.get("name", ""))]
        logging.info(f"Filtered stacks: {original_count} -> {len(data['stacks'])} (pattern: {pattern_str})")
        return {s.get("_source_id") for s in data.get("stacks", [])}

    def _get_relationship_id(self, obj: dict, relationship_name: str) -> str | None:
        """Extract _source_id from a relationship, handling both dict and string formats."""
        rel = obj.get("_relationships", {}).get(relationship_name)
        if rel is None:
            return None
        if isinstance(rel, dict):
            return rel.get("_source_id")
        return rel

    def _filter_stack_variables(self, data: dict, included_stack_ids: set) -> None:
        """Filter stack_variables to only those belonging to included stacks."""
        if not data.get("stack_variables"):
            return
        original_count = len(data["stack_variables"])
        data["stack_variables"] = [
            v for v in data["stack_variables"]
            if self._get_relationship_id(v, "stack") in included_stack_ids
        ]
        logging.info(f"Filtered stack_variables: {original_count} -> {len(data['stack_variables'])}")

    def _filter_modules(self, data: dict, pattern_str: str) -> set:
        """Filter modules by name pattern and return set of included module IDs."""
        pattern = re.compile(pattern_str)
        original_count = len(data.get("modules", []))
        data["modules"] = [m for m in data.get("modules", []) if pattern.match(m.get("name", ""))]
        logging.info(f"Filtered modules: {original_count} -> {len(data['modules'])} (pattern: {pattern_str})")
        return {m.get("_source_id") for m in data.get("modules", [])}

    def _filter_contexts(self, data: dict, included_stack_ids: set) -> set:
        """Filter contexts keeping auto-attached ones and those attached to included stacks."""
        if not data.get("contexts"):
            return set()

        original_count = len(data["contexts"])
        filtered_contexts = []

        for ctx in data["contexts"]:
            labels = ctx.get("labels", [])
            is_auto_attached = any("autoattach:" in str(label) for label in labels)

            if is_auto_attached:
                filtered_contexts.append(ctx)
                continue

            attached_stacks = ctx.get("_relationships", {}).get("stacks", [])
            if attached_stacks:
                filtered_attached = [s for s in attached_stacks if s.get("_source_id") in included_stack_ids]
                if filtered_attached:
                    ctx["_relationships"]["stacks"] = filtered_attached
                    filtered_contexts.append(ctx)

        data["contexts"] = filtered_contexts
        logging.info(f"Filtered contexts: {original_count} -> {len(data['contexts'])}")
        return {c.get("_source_id") for c in data.get("contexts", [])}

    def _filter_context_variables(self, data: dict, included_context_ids: set) -> None:
        """Filter context_variables to only those belonging to included contexts."""
        if not data.get("context_variables"):
            return
        original_count = len(data["context_variables"])
        data["context_variables"] = [
            v for v in data["context_variables"]
            if self._get_relationship_id(v, "context") in included_context_ids
        ]
        logging.info(f"Filtered context_variables: {original_count} -> {len(data['context_variables'])}")

    def _filter_spaces(self, data: dict) -> None:
        """Filter spaces to only those containing included stacks or modules."""
        if not data.get("spaces"):
            return

        space_ids_with_stacks = {self._get_relationship_id(s, "space") for s in data.get("stacks", [])}
        space_ids_with_modules = {self._get_relationship_id(m, "space") for m in data.get("modules", [])}
        included_space_ids = space_ids_with_stacks | space_ids_with_modules

        original_count = len(data["spaces"])
        data["spaces"] = [s for s in data["spaces"] if s.get("_source_id") in included_space_ids]
        logging.info(f"Filtered spaces: {original_count} -> {len(data['spaces'])}")

    def _process_data(self, data: dict, include_config: Optional[dict] = None) -> dict:
        """Filter data based on include patterns from config."""
        if not include_config:
            logging.info("No include filters specified. Using all data.")
            return data

        logging.info("Start filtering data based on include patterns")

        if include_config.get("workspaces"):
            included_stack_ids = self._filter_stacks(data, include_config["workspaces"])
        else:
            included_stack_ids = {s.get("_source_id") for s in data.get("stacks", [])}

        self._filter_stack_variables(data, included_stack_ids)

        if include_config.get("modules"):
            self._filter_modules(data, include_config["modules"])

        included_context_ids = self._filter_contexts(data, included_stack_ids)
        self._filter_context_variables(data, included_context_ids)
        self._filter_spaces(data)

        logging.info("Stop filtering data based on include patterns")

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

    def generate(self,
                 extra_vars: Optional[dict] = None,
                 template_name: str = "main.tf.jinja",
                 generation_config: Optional[dict] = None,
                 include_config: Optional[dict] = None):
        if generation_config is None:
            generation_config = {}
        if extra_vars is None:
            extra_vars = {}

        self._check_requirements()
        data = self._load_data()
        data = self._process_data(data, include_config)
        self._generate_code(
            data=data,
            extra_vars=extra_vars,
            template_name=template_name,
            generation_config=generation_config
        )
        self._format_code()
        self._validate_code()
