"""
Module contains data manager class for the Projects database. Also includes the JsonDataAccessor class that directly
interfaces with the JSON database. The _get_data_accessor() function is a factory function that returns the appropriate
data accessor based on the current configuration, which could be useful in the case that we have more than one data
accessor type. In the future, this could be a constructor argument for the ProjectDataManager class.
"""
import json
import os
from typing import *

from core import constants, project, shot, assetEntry
from core.hutils import logger, system
from assets import asset, usdAsset, reviewable, projectFile, imageSequence

log = logger.setup_logger()
log.debug("data_manager.py loaded")


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
            "ARCHIVE_DB_PATH": '/Users/hunterwilliams/Documents/project_db/projects_archive.json',
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


class ProjectDataManager:
    """
    Projects data manager. This is used as the primary interface for the Project's database. Uses the
    AbstractDataAccessor interface to access the database directly.
    """

    def __init__(self):
        self.accessor = JsonDataAccessor(ConfigDataManager().get_config_filepath('DB_PATH').system_path())
        self.data = self.accessor.data
        self.archive_accessor = JsonDataAccessor(ConfigDataManager().get_config_filepath('ARCHIVE_DB_PATH').system_path())

    def __repr__(self) -> str:
        return f" Project Manager @ {self.accessor.db_path}"

    def save(self) -> bool:
        """
        Saves the current state of our data to the database via the specific implementation of the DataAccessor.
        :return: True if successful
        """
        for project_inst in self.get_projects():
            self.update_project(project_inst, push=False)

        return self.accessor.save_data(self.data)

    def get_projects(self) -> List[project.Project]:
        """
        Builds a list of project.Project objects from the current data.
        """
        project_list = []
        project_count = len(self.data.items())
        if project_count == 0:
            log.warning(f"No projects found in database at path {self.accessor.db_path}")
            return []

        for key, val in self.data.items():
            project_list.append(project.Project.from_dict(val))

        return project_list

    def get_project_names(self) -> List[str]:
        """
        Builds a list of project names from the current data.
        :return: list of project names
        """
        return [project_instance.name for project_instance in self.get_projects()]

    def get_project(self, project_name: str) -> project.Project:
        """
        Builds a project.Project object from the current data given a project name.
        param str project_name: name of project
        """
        for project_instance in self.get_projects():
            if project_instance.name == project_name:
                return project_instance

        raise ValueError(f"Project {project_name} not found in database at path {self.accessor.db_path}")

    def is_project(self, project_name: str) -> bool:
        """
        Checks if a project exists in the database given a project name.
        param str project_name: name of project
        :return: True if project exists
        """
        return project_name in self.data.keys()

    def update_project(self, project_to_update: project.Project, push: bool = True) -> bool:
        """
        Updates a project in the database given a project instance. This is the primary method for updating a project.
        :param project.Project project_to_update: project instance to be updated in the database
        :param bool push: if True, pushes the updated project back to the database
        """
        project_name = project_to_update.name

        if project_name not in self.data.keys():
            log.warning(f"Project {project_name} not found in database at path {self.accessor.db_path}")
            return False

        self.data[project_name] = project_to_update.to_dict()

        if push:
            return self.save()

        return True

    def add_project(self, project_instance: project.Project, push: bool = True) -> bool:
        """
        Adds a project to the database given a project instance. This is the primary method for adding a project.
        param project.Project project_instance: project instance to be added to the database
        param bool push: if True, pushes the updated project back to the database
        :return: True if successful
        """

        if self.is_project(project_instance.name):
            log.warning(f"Project {project_instance.name} already exists in database at path {self.accessor.db_path}")
            return False

        log.info(f"Adding project {project_instance.name} to database at path {self.accessor.db_path}")
        self.data[project_instance.name] = project_instance.to_dict()

        ProjectDirectoryGenerator(project_instance, push_directories=True)

        if push:
            return self.save()

        return True

    def add_shot(self, project_instance: project.Project, shot_instance: shot.Shot, push: bool = True) -> bool:
        """
        Adds a shot to the database given a project instance and a shot instance. This is the primary method for adding
        a shot.
        """
        if not self.is_project(project_instance.name):
            log.warning(f"Project {project_instance.name} does not exist in database at path {self.accessor.db_path}")
            return False

        if shot_instance.name in [s.name for s in project_instance.get_shots()]:
            log.warning(f"Shot {shot_instance.name} already exists in project {project_instance.name} in database at "
                        f"path {self.accessor.db_path}")
            return False

        log.info(f"Adding shot {shot_instance.name} to project {project_instance.name} in database at "
                 f"path {self.accessor.db_path}")

        project_instance.add_shot(shot_instance)
        self.update_project(project_instance, push=False)

        ProjectDirectoryGenerator(project_instance, shot_instance, push_directories=True)

        if push:
            return self.save()

        return True

    def project_from_filepath(self, filepath: str) -> project.Project:
        """
        Builds a project.Project object from a filepath.
        param str filepath: filepath to build project from
        :return: project.Project object
        """
        path_elements = filepath.split(os.sep)
        project_index = path_elements.index(constants.PROJECTS_DIR_NAME)

        if project_index == -1:
            raise ValueError(f"Filepath {filepath} does not contain a project folder")

        if project_index + 2 >= len(path_elements):
            raise ValueError(f"Filepath {filepath} does not contain a project name")

        project_name = path_elements[project_index + 2]

        log.debug(f"Building project from filepath: {filepath}")

        return self.get_project(project_name)

    def shot_from_filepath(self, filepath: str) -> shot.Shot:
        """
        Builds a shot.Shot object from a filepath.
        param str filepath: filepath to build shot from
        :return: shot.Shot object
        """

        path_project = self.project_from_filepath(filepath)

        path_elements = filepath.split(os.sep)
        shot_index = path_elements.index(constants.SHOT_FOLDER)

        if shot_index == -1:
            raise ValueError(f"Filepath {filepath} does not contain a shot folder")

        if shot_index + 1 >= len(path_elements):
            raise ValueError(f"Filepath {filepath} does not contain a shot name")

        shot_name = path_elements[shot_index + 1]

        log.debug(f"Building shot from filepath: {filepath}")
        return path_project.get_shot(shot_name)

    def remove_project(self, project_to_remove: project.Project, push: bool = True, archive_project=False) -> bool:
        """
        Removes a project from the database given a project instance. This is the primary method for removing a project.
        param project.Project project_to_remove: project instance to be removed from the database
        param bool push: if True, pushes the updated project back to the database
        param bool archive_project: if True, archives the project to the archive directory
        :return: True if successful
        """

        project_name = project_to_remove.name
        if project_name not in self.data.keys():
            log.warning(f"Project {project_name} not found in database at path {self.accessor.db_path}")
            return False

        log.warning(f"Removing project {project_name} from database at path {self.accessor.db_path}")
        self.data.pop(project_name)

        if archive_project:
            log.warning(f"Archiving project {project_name}")
            raise NotImplementedError

        if push:
            return self.save()

        return True

    def remove_shot(self, shot_to_remove: shot.Shot, push: bool = True) -> bool:
        """
        Removes a shot from the database given a project instance and a shot instance. This is the primary method for
        removing a shot.
        param shot.Shot shot_to_remove: shot instance to be removed
        param bool push: if True, pushes the updated project back to the database
        :return: True if successful
        """
        parent_project = shot_to_remove.project
        project_name = parent_project.name

        if project_name not in self.data.keys():
            log.warning(f"Project {project_name} not found in database at path {self.accessor.db_path}")
            return False

        if shot_to_remove.name not in self.data[project_name]["shots"].keys():
            log.warning(f"Shot {shot_to_remove.name} not found in project {project_name} in database at "
                        f"path {self.accessor.db_path}")
            return False

        log.warning(f"Removing shot {shot_to_remove.name} from project {project_name} in database at "
                    f"path {self.accessor.db_path}")

        self.data[project_name]["shots"].pop(shot_to_remove.name)

        if push:
            return self.save()

        return True

    def backup(self) -> bool:
        """
        Backs up the database to json. This is the primary method for backing up the database. If it's mongodb, it will
        be backed up to json. If it's json, it will be backed up to json.
        """
        return self.accessor.backup(increment=True)

    def archive_project(self, project_to_archive: project.Project) -> bool:
        """
        Archives a project by moving it to the archive database.
        :param project.Project project_to_archive: project to archive
        :return: True if successful
        """
        log.debug(f"Archiving project {project_to_archive.name}")
        self.archive_accessor.data[project_to_archive.name] = self.data.pop(project_to_archive.name)
        self.save()
        self.archive_accessor.save_data(self.archive_accessor.data)
        return True

    def unarchive_project(self, project_to_unarchive: project.Project) -> bool:
        """
        Unarchives a project by moving it from the archive database to the main database.
        :param project.Project project_to_unarchive: project to unarchive
        :return: True if successful
        """
        log.debug(f"Unarchiving project {project_to_unarchive.name}")
        self.data[project_to_unarchive.name] = self.archive_accessor.data.pop(project_to_unarchive.name)
        self.save()
        self.archive_accessor.save_data(self.archive_accessor.data)
        return True

    def get_archive_projects(self):
        """
        Builds a list of project.Project objects from the current data.
        """
        project_list = []
        project_count = len(self.archive_accessor.data.items())
        if project_count == 0:
            log.warning(f"No projects found in database at path {self.accessor.db_path}")
            return []

        for key, val in self.archive_accessor.data.items():
            project_list.append(project.Project.from_dict(val))

        return project_list

    def get_archive_project(self, project_name: str) -> project.Project:
        """
        Builds a project.Project object from the current data given a project name.
        param str project_name: name of project
        """
        for project_instance in self.get_archive_projects():
            if project_instance.name == project_name:
                return project_instance

        raise ValueError(f"Project {project_name} not found in database at path {self.archive_accessor.db_path}")


class ProjectDirectoryGenerator:
    """
    Generates directory structures for projects and shots.
    """
    def __init__(self, project_instance: Union[project.Project, None] = None,
                 shot_instance: Union[shot.Shot, None] = None, push_directories: bool = False):

        if not project_instance and not shot_instance:
            raise ValueError("Either a project or shot instance must be provided.")

        self.project_structure: dict[Any, Dict[Any, Any]] = constants.PROJECT_STRUCTURE.copy()
        self.shot_structure: dict[Any, Dict[Any, Any]] = constants.SHOT_STRUCTURE.copy()

        if project_instance and not shot_instance:
            self.project = project_instance
            self.set_project_directories()
            if push_directories:
                self.push_project_directories()

        if shot_instance and not project_instance:
            self.shot = shot_instance
            self.project = self.shot.project
            self.set_shot_directories(shot_instance)

    def set_project_directories(self) -> bool:
        """
        Generates the directories for a project instance.
        :return: True if successful
        """
        root_constant = constants.PROJECTS_ROOT

        project_name = self.project.name
        year = self.project.year

        project_path = f'{root_constant}/{year}/{project_name}'
        self.project_structure[project_path] = self.project_structure.pop("name")

        for key, value in self.project_structure[project_path].items():
            self.project_structure[project_path][key] = f"{project_path}/{key}"

        log.info(f"Generating directories for project {project_name}")
        log.debug(f"Project structure: {self.project_structure}")

        _generate_directories(self.project_structure)

        return True

    def push_project_directories(self) -> bool:
        """
        Verifies the directories for a project instance.
        :return: True if successful
        """
        if not len(self.project.get_shots()) > 1:
            log.debug(f"Project {self.project.name} has no shots. Skipping verification.")
            return False

        for shot_instance in self.project.get_shots():
            self.shot = shot_instance
            self.project = self.shot.project
            self.set_shot_directories(shot_instance)

        return True

    def set_shot_directories(self, shot_instance: shot.Shot) -> bool:
        """
        Generates the directories for a shot instance.
        :return: True if successful
        """
        root_constant = constants.PROJECTS_ROOT
        self.shot_structure = constants.SHOT_STRUCTURE.copy()

        project_name = self.project.name
        year = self.project.year
        shot_name = shot_instance.name

        shot_path = f'{root_constant}/{year}/{project_name}/shots/{shot_name}'
        self.shot_structure[shot_path] = self.shot_structure.pop("name")

        for key, value in self.shot_structure[shot_path].items():
            if isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    # TODO: fix typing here
                    self.shot_structure[shot_path][key][sub_key] = f"{shot_path}/{key}/{sub_key}"  # type: ignore
            else:
                self.shot_structure[shot_path][key] = f"{shot_path}/{key}"

        _generate_directories(self.shot_structure)

        return True


class AssetDataManager:
    """
    Assets data manager. This is used as the primary interface for the Asset database. Uses the
    AbstractDataAccessor interface to access the database directly.
    """
    def __init__(self):
        self.accessor = JsonDataAccessor(ConfigDataManager().get_config_filepath('ASSET_DB_PATH').system_path())
        self.data = self.accessor.data
        # self.archive_accessor = JsonDataAccessor(constants.ARCHIVE_ASSET_PATH)

    def __repr__(self) -> str:
        return f" Asset Data Manager @ {self.accessor.db_path}"

    def add_asset(self, assetEntry: assetEntry.AssetEntry) -> bool:
        """
        Adds an asset to the database.
        :param asset_instance: asset instance to add
        :return: True if successful
        """

        if assetEntry.asset_instance.asset_name in self.data.keys():
            raise ValueError(f"Asset {assetEntry.asset_instance.asset_name} already exists in database at path {self.accessor.db_path}")

        self.data[assetEntry.asset_instance.asset_name] = assetEntry.to_dict()
        self.save()
        return True

    def get_assets(self) -> List[assetEntry.AssetEntry]:
        """
        Builds a list of AssetEntry objects from the current data.
        :returns: list of AssetEntry objects
        """
        asset_list = []
        asset_count = len(self.data.items())
        if asset_count == 0:
            log.warning(f"No assets found in database at path {self.accessor.db_path}")
            return []

        log.debug(f"Found Assets: {self.data}")
        for key, val in self.data.items():
            asset_list.append(assetEntry.AssetEntry.from_dict(val))

        return asset_list

    def get_asset(self, asset_name: str) -> Union[None, 'asset.Asset']:
        """
        Builds an asset.Asset object from the current data given an asset name.
        """
        for assetEntry in self.get_assets():
            if assetEntry.asset_instance.asset_name == asset_name:
                return assetEntry.asset_instance
        return None

    def save(self) -> bool:
        """
        Saves the current state of our data to the database via the specific implementation of the DataAccessor.
        :return: True if successful
        """
        for asset_instance in self.get_assets():
            self.update_asset(asset_instance, push=False)

        return self.accessor.save_data(self.data)

    def update_asset(self, asset_to_update: assetEntry.AssetEntry, push: bool = True) -> bool:
        """
        Updates an asset in the database given a asset instance. This is the primary method for updating an asset.
        :param assetEntry.AssetEntry asset_to_update: asset instance to be updated in the database
        :param bool push: if True, pushes the updated project back to the database
        """
        asset_name = asset_to_update.asset_instance.asset_name

        if asset_name not in self.data.keys():
            log.warning(f"Project {asset_name} not found in database at path {self.accessor.db_path}")
            return False

        self.data[asset_name] = asset_to_update.to_dict()

        if push:
            return self.save()

        return True


class AssetDirectoryGenerator:
    """
    Generates directory structures for Assets
    """
    def __init__(self, asset_instance: asset.Asset):

        self.asset = asset_instance
        self.asset_structure: dict[Any, Dict[Any, Any]] = constants.ASSET_STRUCTURE.copy()
        self.set_asset_directories()
        self.asset_name = f"{self.asset.asset_type}_{self.asset.asset_name}"

    def set_asset_directories(self) -> bool:
        """
        Generates the directories for an asset instance.
        :return: True if successful
        """
        root_constant = ConfigDataManager().get_config_directory('ASSETS_ROOT').system_path()

        asset_path = f'{root_constant}/{self.asset_name}'
        self.asset_structure[asset_path] = self.asset_structure.pop("name")

        for key, value in self.asset_structure[asset_path].items():
            self.asset_structure[asset_path][key] = f"{asset_path}/{key}"

        log.info(f"Generating directories for Asset {self.asset_name}")
        log.debug(f"Project structure: {self.asset_structure}")

        _generate_directories(self.asset_structure)

        return True


def _generate_directories(folder_dictionary) -> bool:
    """
    Generates directories for a given folder dictionary.
    :param dict folder_dictionary: folder dictionary to generate directories for
    :return: True if successful
    """

    warnings: List[str] = []
    info: List[str] = []

    for key, value in folder_dictionary.items():
        if isinstance(value, dict):
            _generate_directories(value)
        else:
            if not os.path.exists(value):
                os.makedirs(value, exist_ok=True)
                info.append(value)
            warnings.append(value)

    log.info(f'Generated {len(info)} directories: {info}')
    log.warning(f'Skipped {len(warnings)} directories: {warnings}')

    return True


