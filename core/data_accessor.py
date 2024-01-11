import json
import os
from typing import *

from core.hutils import logger, system

log = logger.setup_logger()
log.debug("data_accessor.py loaded")


class JsonDataAccessor:
    """
    Json data accessor subclass of AbstractDataAccessor. This is used as the primary interface for the
    Project's database via json.
    """

    def __init__(self, db_path, create_if_missing: bool = True, default_data: Any = None):
        self.db_path = system.Filepath(db_path).system_path()
        self.default_data = default_data
        self.create_if_missing = create_if_missing
        self.data = self.get_data()

    def get_data(self) -> dict:
        """
        Gets the database data and returns it as a dictionary.
        :return: dictionary of database data
        """
        if not os.path.exists(self.db_path):
            log.error(f"Database file does not exist: {self.db_path}")
            if self.create_if_missing:
                json_filepath = system.Filepath(self.db_path).system_path()
                if not os.path.exists(os.path.dirname(json_filepath)):
                    os.makedirs(os.path.dirname(json_filepath), exist_ok=True)
                with open(json_filepath, 'w') as fileName:
                    if not self.default_data:
                        self.default_data = {}
                    json.dump(self.default_data, fileName, indent=4)
                    log.warning(f"Created database file: {self.db_path}")
            return {}
        with open(self.db_path, 'r') as fileName:
            self.data = json.load(fileName)
        return self.data

    def save_data(self, data: dict) -> bool:
        """
        Saves the database data to disk.
        :param dict data: dictionary of database data
        :return: True if successful
        """
        with open(self.db_path, 'w') as fileName:
            json.dump(data, fileName, indent=4)

        return True

    def backup(self, increment: bool = True) -> bool:
        """
        Backs up the database to a json file in the backup directory.
        param increment: bool whether to increment the backup file name
        :return: True if successful
        """
        raise NotImplementedError("Backup not implemented yet")