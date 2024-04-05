import logging

import click
import requests
from click_help_colors import HelpColorsCommand
from requests_toolbelt.utils import dump as request_dump

from spacemk import load_normalized_data
from spacemk.spacelift import Spacelift


def _get_repository_tags(endpoint: str, github_api_token: str, namespace: str, repository: str) -> dict:
    data = {}

    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {github_api_token}",
    }

    try:
        url = f"{endpoint}/repos/{namespace}/{repository}/tags?per_page=100"
        response = requests.get(headers=headers, url=url)
        logging.debug(request_dump.dump_all(response).decode("utf-8"))
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        raise RuntimeError(f"HTTP Error: {e}") from e

    for tag in response.json():
        tag_name = tag.get("name").removeprefix("v")
        data[tag_name] = tag["commit"]["sha"]

    return data


@click.command(
    cls=HelpColorsCommand,
    help="Create module versions.",
    help_headers_color="yellow",
    help_options_color="green",
)
@click.decorators.pass_meta_key("config")
def create_module_versions(config):
    data = load_normalized_data()

    if "modules" not in data:
        logging.warning("No modules found. Skipping.")

    spacelift = Spacelift(config.get("spacelift"))

    for module in data.get("modules"):
        if module.get("vcs.repository") is None:
            logging.warning(f"Module '{module.get('name')}' has no repository information. Skipping")
            continue

        tags = _get_repository_tags(
            endpoint=config.get("github.endpoint", "https://api.github.com"),
            github_api_token=config.get("github.api_token"),
            namespace=module.get("vcs.namespace"),
            repository=module.get("vcs.repository"),
        )

        for tag, commit_sha in tags.items():
            spacelift.create_module_version(
                commit_sha=commit_sha,
                module=module.get("name"),
                version=tag,
            )
