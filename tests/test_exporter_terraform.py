import os

import pytest
from rich.console import Console

from spacemk.exporters import load_exporter


@pytest.fixture(scope="session")
def vcr_config():
    return {"filter_headers": ["authorization"]}


@pytest.mark.vcr()
def test_tfe_organization():
    config = {"name": "terraform", "settings": {"api_token": os.getenv("TF_API_TOKEN")}}
    console = Console()
    exporter = load_exporter(config, console)
    organizations = exporter._list_organizations()  # noqa: SLF001
    print(organizations)
