import click
import yaml

@click.command(help="Generate configuration file")
@click.option("--file", default="config.yml", help="Path to the configuration file.", type=click.Path())
def config(file):
    # TODO: Check if the file exists and if so ask the user if they want to overwrite it

    # TODO: Ask questions to dynamically build this file
    data = {
        "exporter": {
            "api_token": "$TFC_API_TOKEN",
            "organizations": [
                "example-org-f50608"
            ],
            "name": "tfc",
        }
    }

    with open(file, mode="wb") as f:
        yaml.safe_dump(data, f, encoding="utf-8", sort_keys=True)

    print("Config")
