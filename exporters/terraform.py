import click
import requests
from .base import BaseExporter


class TerraformExporter(BaseExporter):
    def __init__(self, ctx, settings, flavor):
        super(TerraformExporter, self).__init__(ctx, settings)
        self.flavor = flavor

    def __call_api(self, path, method="GET", payload=None, ignore_errors=False):
      headers = {
        "Authorization": f"Bearer {self.settings['api_token']}",
        "Content-Type": "application/vnd.api+json",
      }

      base_url = self.settings["api_url"] if "api_url" in self.settings else "https://app.terraform.io/api/v2"
      url = f"{base_url}{path}"

      response = requests.request(method, url, json=payload, headers=headers)
      if response.ok or ignore_errors:
        return response.json(), response
      else:
        raise click.ClickException(f"Query to {path} failed with code of {response.status_code}")

    def _check_prerequisites(self):
      #  Check connection to the TFC/TFE API
       _, response = self.__call_api("/account/details", ignore_errors=True)
       if response.status_code != 200:
          platform_name = "Terraform Cloud" if self.flavor == "tfc" else "Terraform Enterprise"
          raise click.ClickException(f"Could not connect to the {platform_name} API (Status Code: {response.status_code})")

    def _export_data(self):
        """Export data"""
        self.ctx.item("Exporting projects", level=2)
        self.ctx.success()
        self.ctx.item("Exporting workspaces", level=2)
        self.ctx.success()
        self.ctx.item("Exporting variables", level=2)
        self.ctx.success()
