import os

import pytest
from rich.console import Console

from spacemk.exporters import load_exporter


@pytest.fixture(scope="module")
def console():
    return Console()


@pytest.fixture(scope="module")
def terraform_exporter(console, terraform_exporter_config):
    return load_exporter(terraform_exporter_config, console)


@pytest.fixture(scope="module")
def terraform_exporter_config():
    return {
        "name": "terraform",
        "settings": {
            "api_endpoint": os.getenv("TF_API_ENDPOINT", "https://app.terraform.io"),
            "api_token": os.getenv("TF_API_TOKEN", "example_token"),
        },
    }


@pytest.fixture(scope="module")
def vcr_config():
    return {"block_network": True, "filter_headers": ["Authorization", "User-Agent"], "record_mode": "once"}
