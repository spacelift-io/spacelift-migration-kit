import json
import logging
from abc import ABC, abstractmethod
from functools import reduce
from pathlib import Path

import click
import xlsxwriter


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

    def _display_report(self, data: dict) -> None:
        """Display data report in the terminal

        Args:
            data (dict): Source provider entity data
        """
        logging.info("Default report display")

        logging.debug("Start displaying report")

        for entity_type, entity_list in sorted(data.items()):
            title = entity_type.replace("_", " ").title()
            count = len(entity_list)

            count_with_warnings = len([e for e in entity_list if "warnings" in e and len(e["warnings"]) > 0])
            if count_with_warnings > 0:
                self._print(f"{title}: {count} (including {count_with_warnings} with warnings)")
            else:
                self._print(f"{title}: {count}")

        logging.debug("Stop displaying report")

    def _enrich_data(self, data: dict) -> dict:
        """Enrich source provider data

        Args:
            data (dict): Source provider data

        Returns:
            dict: Enriched source provider data
        """
        logging.info("No data enrichment implemented")
        return data

    def _ensure_tmp_folder_exists(self) -> Path:
        logging.debug("Start ensuring the 'tmp' folder exists")

        folder = Path(f"{__file__}/../../../tmp").resolve()
        if not Path.exists(folder):
            logging.info("Creating 'tmp' folder")
            Path.mkdir(folder, parents=True)
        else:
            logging.info("The 'tmp' folder already exists. Skipping creation.")

        logging.debug("Stop ensuring the 'tmp' folder exists")

        return folder

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

    def _save_data_to_file(self, data: dict) -> None:
        """Save the Spacelift entities data to a JSON file

        Args:
            data (dict): Spacelift entities data
        """
        logging.debug("Start saving data to file")

        folder_path = self._ensure_tmp_folder_exists()

        with Path(f"{folder_path}/data.json").open("w") as fp:
            json.dump(data, fp, indent=2, sort_keys=True)

        logging.debug("Stop saving data to file")

    def _save_report_to_file(self, data: dict) -> None:
        """Save source provider data report to file

        Args:
            data (dict): Source provider entity data
        """
        logging.info("Default report saving to file")

        logging.debug("Start saving report to file")

        folder_path = self._ensure_tmp_folder_exists()
        workbook = xlsxwriter.Workbook(f"{folder_path}/report.xlsx")

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
                    column += 1

        workbook.close()

        logging.debug("Stop saving report to file")

    def audit(self) -> None:
        """Audit the source provider data

        A report is displayed in the terminal, and optionally, the extracted data can be saved to file.
        """
        logging.debug("Start auditing data")

        data = self._extract_data()
        data = self._filter_data(data)
        data = self._check_data(data)
        self._save_report_to_file(data)
        self._display_report(data)

        logging.debug("Stop auditing data")

    def export(self) -> None:
        """Export data from the source provider and map it to Spacelift entitty types"""
        logging.debug("Start exporting data")

        data = self._extract_data()
        data = self._filter_data(data)
        data = self._enrich_data(data)
        data = self._map_data(data)
        self._save_data_to_file(data)

        logging.debug("Stop exporting data")
