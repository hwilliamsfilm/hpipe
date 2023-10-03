"""
Houdini module to get information about the current session

PROJECT FILE -> ../../../shot_task_desc_version.hiplc
"""
import hou
from assets import projectFile
from core.hutils import logger, system
from core import data_manager

from typing import *

log = logger.setup_logger()
log.debug("session.py loaded")


class HoudiniSession:
    """
    Class representing the current houdini session.
    """
    def __init__(self):
        self.database = data_manager.ProjectDataManager()
        self.config = data_manager.ConfigDataManager()
        self.projectFile = self.get_project_file()
        self.version = self.get_version()

    def get_project_file(self) -> Union[None, 'projectFile.GenericProjectFile']:
        """
        Gets the current project file as a project file object.
        :returns: The current project file as a project file object or None if the project file is not set.
        """
        path = hou.hipFile.path()
        log.debug(f"Current project file path: {path}")
        filepath = system.Filepath(path)
        if "untitled" in filepath.system_path():
            return None
        return projectFile.project_file_from_filepath(filepath)

    def get_version(self):
        """
        Gets the current version of the project file.
        :returns: The current latest version of the project file given the task and desc or None if the project file is not set.
        """
        if not self.projectFile:
            return None

        hip_directory = self.projectFile.filepath.get_parent_directory()
        hip_files = projectFile.project_files_from_directory(hip_directory)

        log.debug(f"Hip files: {hip_files}")

        current_task = hou.getenv('TASK')
        current_description = hou.getenv('DESCRIPTION')

        matching_hipfiles = []
        for hip_file in hip_files:
            if hip_file.get_asset_description() == current_description and hip_file.get_asset_name() == current_task:
                matching_hipfiles.append(hip_file)

        log.debug(f"Matching hipfiles: {matching_hipfiles}")

        if len(matching_hipfiles) == 0:
            return None

        latest_version: Union[None, tuple[str, int]] = None
        for hip_file in matching_hipfiles:
            version = hip_file.get_version()
            if not latest_version:
                latest_version = version
            elif version[1] > int(latest_version[1]):
                latest_version = version

        return latest_version

    def get_asset_name(self) -> Union[None, str]:
        """
        Gets the name of the current asset.
        :returns: The name of the current asset (task) given the filename or None if the project file is not set.
        """
        if not self.projectFile:
            return None
        return self.projectFile.asset_name

    def get_asset_description(self) -> Union[None, str]:
        """
        Gets the description of the current asset.
        :returns: The description of the current asset given the filename or None if the project file is not set.
        """
        if not self.projectFile:
            return None
        return self.projectFile.get_asset_description()

    def get_filepath(self) -> Union[None, 'system.Filepath']:
        """
        Gets the filepath of the current project file.
        :returns: The filepath of the current project file given the environment variables.
        """
        project_name = hou.getenv('PROJECT')
        shot_name = hou.getenv('SHOT')
        task_name = hou.getenv('TASK')
        description = hou.getenv('DESCRIPTION')
        version_letter, version_number = self.version

        if not self.version:
            version_letter, version_number = 'A', 1

        padded_version_number = str(version_number).zfill(3)

        if not project_name or not shot_name or not task_name:
            log.warning("Could not get project, shot, or task name.")
            return None

        project_instance = self.database.get_project(project_name)
        project_path = project_instance.get_project_path()

        path = f"{project_path}/shots/{shot_name}/working_files/houdini/{shot_name}_{task_name}_{description}_{version_letter}{padded_version_number}.hiplc"

        return system.Filepath(path)

    def get_project(self) -> Union[None, 'project.Project']:
        """
        Gets the project object of the current project file.
        :returns: The project object of the current project file or None if the project file is not set.
        """
        if not self.projectFile:
            return None
        return self.database.get_project(self.projectFile.get_asset_project())

    def get_shot(self) -> Union[None, 'shot.Shot']:
        """
        Gets the shot object of the current project file.
        :returns: The shot object of the current project file or None if the project file is not set.
        """
        if not self.projectFile:
            return None
        if not self.get_project():
            return None
        return self.get_project().get_shot(self.projectFile.get_asset_shot())
