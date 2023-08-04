from .interface import ExporterInterface

class TerraformCloudExporter(ExporterInterface):
    def __init__(self, organization_id):
        self.organization_id = organization_id

    """Export data from Terraform Cloud/Enterprise"""
    def export_data(self):
        """Export data from the current provider"""
        print("Export from TFC/TFE")
        return {}
