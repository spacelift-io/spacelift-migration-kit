import logging
from abc import ABC, abstractmethod
from functools import reduce
from pathlib import Path

import click
import xlsxwriter

from spacemk import get_tmp_folder, save_normalized_data


class BaseExporter(ABC):
    def __init__(self, config: dict):
        """Constructor

        Args:
            config (dict): Exporter configuration
        """
        self._config = config

    def _check_data(self, data: dict) -> dict:
        """Check source provider data and add warnings as needed

        Args:
            data (dict): Source provider entity data

        Returns:
            dict: Source provider entity data, augmented with warnings
        """
        logging.info("No data checks implemented. Skipping.")
        return data

    def _check_requirements(self, action: str) -> None:  # noqa: ARG002
        """Check if the exporter requirements are met

        Args:
            action (str): Type of action to perform. Valid values are "audit" and "export".
        """
        logging.info("No requirement checks defined. Skipping.")

    def _display_report(self, data: dict) -> None:
        """Display data report in the terminal

        Args:
            data (dict): Source provider entity data
        """
        logging.info("Start displaying default report")

        for entity_type, entity_list in sorted(data.items()):
            title = entity_type.replace("_", " ").title()
            count = len(entity_list)

            count_with_warnings = len([e for e in entity_list if "warnings" in e and len(e["warnings"]) > 0])
            if count_with_warnings > 0:
                self._print(f"{title}: {count} (including {count_with_warnings} with warnings)")
            else:
                self._print(f"{title}: {count}")

        logging.info("Stop displaying default report")

    def _enrich_data(self, data: dict) -> dict:
        """Enrich source provider data

        Args:
            data (dict): Source provider data

        Returns:
            dict: Enriched source provider data
        """
        logging.info("No data enrichment implemented")
        return data

    @abstractmethod
    def _extract_data(self) -> dict:
        """Extract raw data from the source provider

        Returns:
            dict: Dictionary with entity types as the keys and lists of entities as the values
        """
        pass

    def _filter_data(self, data: dict) -> dict:
        """Remove unwanted entities from source provider data

        Args:
            data (dict): Source provider data

        Returns:
            dict: Filtered source provider data
        """
        logging.info("No custom data filtering implemented. Using default implementation.")

        return data

    @abstractmethod
    def _map_data(self, data: dict) -> dict:
        """Map data from the source provider entity types to Spacelift equivalent entity types

        Args:
            data (dict): Source provider entity data

        Returns:
            dict: Spacelift entity data
        """
        pass

    def _print(self, message: str) -> None:
        """Print message to the terminal

        Args:
            message (str): Message to prijnt to the terminal
        """
        click.echo(message)

    def _save_report_to_file(self, data: dict) -> None:
        """Save source provider data report to file

        Args:
            data (dict): Source provider entity data
        """
        logging.info("Start saving default report to file")

        path = Path(get_tmp_folder(), "report.xlsx")
        workbook = xlsxwriter.Workbook(path)

        for entity_type_name in data:
            worksheet_name = entity_type_name.replace("_", " ").title()
            worksheet = workbook.add_worksheet(name=worksheet_name)

            flatten_entity_type_data = []
            for entity_data in data.get(entity_type_name):
                entity_data.keypath_separator = None
                flatten_entity_type_data.append(entity_data.flatten(separator="."))

            if len(flatten_entity_type_data) > 0:
                pivoted_entity_type_data = {
                    k: [dic[k] for dic in flatten_entity_type_data if k in dic]
                    for k in reduce(set.union, [set(d.keys()) for d in flatten_entity_type_data])
                }

                column = 0
                for key, value in sorted(pivoted_entity_type_data.items()):
                    worksheet.write(0, column, key)
                    worksheet.write_column(1, column, value)
                    column += 1  # noqa: SIM113

        workbook.close()

        logging.info("Stop saving default report to file")

    def audit(self) -> None:
        """Audit the source provider data

        A report is displayed in the terminal, and optionally, the extracted data can be saved to file.
        """
        logging.info("Start auditing data")

        self._check_requirements(action="audit")
        data = self._extract_data()
        data = self._filter_data(data)
        data = self._check_data(data)
        self._save_report_to_file(data)
        self._display_report(data)

        logging.info("Stop auditing data")

    def export(self) -> None:
        """Export data from the source provider and map it to Spacelift entitty types"""
        logging.info("Start exporting data")

        self._check_requirements(action="export")
        data = self._extract_data()
        data = self._filter_data(data)
        data = self._enrich_data(data)
        data = self._map_data(data)
        save_normalized_data(data)

        logging.info("Stop exporting data")
