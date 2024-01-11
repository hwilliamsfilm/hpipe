import os
from typing import *

from core import constants
from core.hutils import logger, system
from core.data_accessor import JsonDataAccessor

log = logger.setup_logger()
log.debug("data_manager.py loaded")


class ConfigDataManager:
    """
    Config data manager. This is used as the primary interface for the configuration of the pipeline. Replaces the
    constants module by storing everything to a json file in the home directory.
    """
    def __init__(self):
        self.default_dict = {
            "PROJECTS_ROOT": 'Y:/projects/',
            "ASSETS_ROOT": 'Y:/_global_assets/assets/',
            "RECYCLE_BIN": 'Y:/projects/_recycle_bin/',
            "SLATE_PATH": 'Y:/_global_assets/slate/slate_A01.png',
            "DB_PATH": 'Y:/project_db/projects_refactor.json',
            "ARCHIVE_DB_PATH": '/Documents/project_db/projects_archive.json',
            "DB_BACKUP": 'Y:/vault/db_backup/',
            "DB_TYPE": 'json',
            "GLOBAL_ASSETS": 'Y:/_global_assets/',
            "ASSET_DB_PATH": 'Y:/project_db/assets.json',
        }
        self.accessor = JsonDataAccessor(constants.CONFIG_PATH,
                                         create_if_missing=True,
                                         default_data=self.default_dict)
        self.data = self.accessor.data

    def __repr__(self) -> str:
        return f" Config Manager @ {self.accessor.db_path}"

    def backup(self) -> bool:
        """
        Backs up the database to json. This is the primary method for backing up the database. If it's mongodb, it will
        be backed up to json. If it's json, it will be backed up to json.
        """
        return self.accessor.backup(increment=True)

    def save(self) -> bool:
        """
        Saves the current state of our data to the database via the specific implementation of the DataAccessor.
        :return: True if successful
        """
        return self.accessor.save_data(self.data)

    def get_config(self, config_name) -> str:
        """
        Gets the database data and returns it as a dictionary.
        :param str config_name: name of config to get
        :return: dictionary of database data
        """
        if config_name not in self.data.keys():
            raise ValueError(f"Config {config_name} does not exist in config file: {self.accessor.db_path}")

        return self.data[config_name]

    def get_config_filepath(self, config_name) -> system.Filepath:
        """
        Gets the database data and returns it as a dictionary.
        :param str config_name: name of config to get
        :return: dictionary of database data
        """
        if config_name not in self.data.keys():
            raise ValueError(f"Config {config_name} does not exist in config file: {self.accessor.db_path}")

        return system.Filepath(self.data[config_name])

    def get_config_directory(self, config_name) -> system.Directory:
        """
        Gets the database data and returns it as a dictionary.
        :param str config_name: name of config to get
        :return: dictionary of database data
        """
        if config_name not in self.data.keys():
            raise ValueError(f"Config {config_name} does not exist in config file: {self.accessor.db_path}")

        return system.Directory(self.data[config_name])

    def set_config(self, config_name: str, data: str) -> bool:
        """
        Saves the database data to disk.
        :param str config_name: name of config to set
        :param dict data: dictionary of database data
        :return: True if successful
        """
        self.data[config_name] = data
        return self.save()

    def get_all_config(self) -> dict:
        """
        Gets the database data and returns it as a dictionary.
        :return: dictionary of database data
        """
        return self.data