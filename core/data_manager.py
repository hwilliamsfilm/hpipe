"""
Module contains data manager class for the Projects database. Also includes the AbstractDataAccessor class to
be used as a base class for all data accessors. The _get_data_accessor() function is a factory function that
returns the appropriate data accessor based on the current configuration. In the future, this could be a constructor
argument for the ProjectDataManager class.
"""

from abc import ABC, abstractmethod
from core import project, shot
from core.hutils import constants, logger
import json
import os

log = logger.setup_logger()
log.debug("data_manager.py loaded")


class AbstractDataAccessor(ABC):
    """
    Abstract class for data accessors. This is the primary interface for the Projects database.
    """

    @abstractmethod
    def get_data(self) -> dict:
        """
        Gets the database data and returns it as a dictionary.
        :return: dictionary of database data
        """
        pass

    @abstractmethod
    def save_data(self, data: dict) -> bool:
        """
        Saves the database data to disk.
        :param dict data: dictionary of database data
        :return: True if successful
        """
        pass

    @abstractmethod
    def backup(self, increment: bool = True) -> bool:
        """
        Backs up the database to a json file in the backup directory.
        param increment: bool whether to increment the backup file name
        :return: True if successful
        """
        pass


class JsonDataAccessor(AbstractDataAccessor):
    """
    Json data accessor subclass of AbstractDataAccessor. This is used as the primary interface for the
    Project's database via json.
    """

    def __init__(self, db_path: str = constants.DB_PATH):
        self.db_path = db_path
        self.data = self.get_data()

    def get_data(self) -> dict:
        """
        Gets the database data and returns it as a dictionary.
        :return: dictionary of database data
        """
        if not os.path.exists(self.db_path):
            log.error(f"Database file does not exist: {self.db_path}")
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


def _get_data_accessor() -> AbstractDataAccessor or None:
    """
    Factory method for data accessor. Returns the appropriate data accessor based on the config.
    :return: AbstractDataAccessor subclass
    """
    if constants.DB_TYPE == 'json':
        return JsonDataAccessor()
    elif constants.DB_TYPE == 'mongodb':
        raise NotImplementedError("MongoDB not implemented yet")
    else:
        raise ValueError(f"Invalid DB_TYPE: {constants.DB_TYPE}")


class ProjectDataManager:
    """
    Projects data manager. This is used as the primary interface for the Project's database. Uses the
    AbstractDataAccessor interface to access the database directly.
    """

    def __init__(self):
        self.accessor = _get_data_accessor()
        self.data = self.load()

    def __repr__(self) -> str:
        return f" Project Manager @ {self.accessor.db_path}"

    def load(self) -> dict:
        """
        Loads the database into memory using the specific implementation of the DataAccessor.
        :return: dictionary of the database
        """
        return self.accessor.get_data()

    def save(self) -> bool:
        """
        Saves the current state of our data to the database via the specific implementation of the DataAccessor.
        :return: True if successful
        """
        return self.accessor.save_data(self.data)

    def get_projects(self) -> list[project.Project]:
        """
        Builds a list of project.Project objects from the current data.
        """
        project_list = []
        project_count = len(self.data.items())
        if project_count == 0:
            log.warning(f"No projects found in database at path {self.accessor.db_path}")
            return []

        for key, val in self.data.items():
            project_list.append(project.Project.from_json(val))

        return project_list

    def get_project(self, project_name: str) -> project.Project or None:
        """
        Builds a project.Project object from the current data given a project name.
        param str project_name: name of project
        """
        for project_instance in self.get_projects():
            if project_instance.name == project_name:
                return project_instance

        log.warning(f"Project {project_name} not found in database at path {self.accessor.db_path}")
        return None

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

        log.warning(f"Updating project {project_name} in database at path {self.accessor.db_path}")
        self.data[project_name] = project_to_update.export_project()

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

        log.warning(f"Adding project {project_instance.name} to database at path {self.accessor.db_path}")
        self.data[project_instance.name] = project_instance.export_project()
        self.build_project_directories(project_instance)

        if push:
            return self.save()

    @staticmethod
    def build_project_directories(project_instance: project.Project) -> bool:
        """
        Builds the project directories for a given project instance.
        param project.Project project_instance: project instance to build directories for
        :return: True if successful
        """
        log.warning(f"Building project directories for {project_instance.name}")
        return False

    @staticmethod
    def build_shot_directories(shot_instance: shot.Shot) -> bool:
        """
        Builds the shot directories for a given shot instance.
        param shot.Shot shot_instance: shot instance to build directories for
        :return: True if successful
        """
        log.warning(f"Building shot directories for {shot_instance.name}")
        return False

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
        project_name = shot_to_remove.project.name

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

