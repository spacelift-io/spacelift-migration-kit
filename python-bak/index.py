import json
from pprint import pprint

from exporters import ExporterInterface, TerraformCloudExporter

class MigrationKit():
    def _load_config(self):
        """Load configuration"""
        path = "config.json"
        with open(path) as file:
          return json.load(file)

    def _get_exporter(self, config) -> ExporterInterface:
      name = config["name"]
      settings = config["settings"]

      if name == "terraform_cloud":
          exporter = TerraformCloudExporter(
            organization_id=settings["organization_id"]
          )
      else:
        raise ValueError(f"Unknown exporter name ({name})")

      return exporter

    def run(self):
      """Migrate from the current provider to Spacelift"""
      try:
        config = self._load_config()

        exporter = self._get_exporter(config["exporter"])
        data = exporter.export_data()

        # pprint(config)
        # pprint(vars(exporter))
        # pprint(data)
      except Exception as e:
         print(f"An error occured: {e}")
         exit(1)

if __name__ == "__main__":
  migration_kit = MigrationKit()
  migration_kit.run()
