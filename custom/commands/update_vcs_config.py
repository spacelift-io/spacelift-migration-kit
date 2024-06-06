import csv
import logging
from pathlib import Path
from urllib.parse import urlparse

import click
from click_help_colors import HelpColorsCommand

from spacemk import get_tmp_folder, load_normalized_data, save_normalized_data


def find_stack_vcs_config(stack_name: str, vcs_config: dict) -> dict | None:
    for item in vcs_config:
        if item.get("WorkspaceName") == stack_name:
            return item

    return None


def load_vcs_config(path: str) -> dict:
    with Path(path).open("r", encoding="utf-8") as fp:
        return list(csv.DictReader(fp))


@click.command(
    cls=HelpColorsCommand,
    help="Update stacks VCS configuration.",
    help_headers_color="yellow",
    help_options_color="green",
)
@click.option(
    "--path",
    "vcs_config_file_path",
    default="vcs_config.csv",
    help="Path to the CSV file containing the VCS configuration.",
    show_default=True,
    type=click.Path(exists=True),
)
def update_vcs_config(vcs_config_file_path: str):
    data = load_normalized_data()
    save_normalized_data(data, Path(get_tmp_folder(), "data.bak.json"))
    vcs_config = load_vcs_config(vcs_config_file_path)

    for stack in data.get("stacks"):
        stack_vcs_config = find_stack_vcs_config(stack.get("name"), vcs_config)
        if not stack_vcs_config:
            logging.warning(f"No VCS configuration found for the '{stack.get('name')}' stack. Skipping.")
            continue

        if stack_vcs_config.get("BackendPath"):
            project_root = "/" + stack_vcs_config.get("BackendPath").strip("/") + "/"
        else:
            project_root = None

        stack.vcs.update(
            {
                "branch": stack_vcs_config.get("Branch"),
                "integration_id": urlparse(stack_vcs_config.get("RepoURL")).path.split("/")[1],
                "namespace": urlparse(stack_vcs_config.get("RepoURL")).path.split("/")[2],
                "project_root": project_root,
                "provider": "azure_devops",
                "repository": stack_vcs_config.get("RepoName"),
            }
        )

    save_normalized_data(data)
