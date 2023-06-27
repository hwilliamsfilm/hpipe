from core.hutils import logger, system
from assets import asset

from typing import *
if TYPE_CHECKING:
    pass

log = logger.setup_logger()
log.debug("projectFile.py loaded")


class GenericProjectFile(asset.Asset):
    """
    Class for a project file. Stores the filepath to the file.
    """
    def __init__(self, filepath: 'system.Filepath', asset_name: str = ''):
        super().__init__(asset_name)
        self.filepath = filepath

    def __repr__(self) -> str:
        return f"ProjectFile <{self.asset_name}> from " \
               f"<{self.filepath.get_parent_directory()}>"


class HoudiniProjectFile(GenericProjectFile):
    """
    Class for a Houdini project file. Stores the filepath to the file.
    """
    def __init__(self, filepath: 'system.Filepath', asset_name: str = ''):
        super().__init__(filepath, asset_name)

    def __repr__(self) -> str:
        return f"HoudiniProjectFile <{self.asset_name}> from " \
               f"<{self.filepath.get_parent_directory()}>"


class NukeProjectFile(GenericProjectFile):
    """
    Class for a Nuke project file. Stores the filepath to the file.
    """
    def __init__(self, filepath: 'system.Filepath', asset_name: str = ''):
        super().__init__(filepath, asset_name)

    def __repr__(self) -> str:
        return f"NukeProjectFile <{self.asset_name}> from " \
               f"<{self.filepath.get_parent_directory()}>"


def project_file_from_filepath(project_filepath: 'system.Filepath') -> 'GenericProjectFile':
    """
    Returns a GenericProjectFile object from a filepath.
    :param project_filepath: Filepath to the project file.
    :return: GenericProjectFile object.
    """
    houdini_project_file_extensions = ['hip', 'hipnc', 'hiplc']
    nuke_project_file_extensions = ['nk', 'nc']

    if project_filepath.get_extension() in houdini_project_file_extensions:
        return HoudiniProjectFile(project_filepath)
    elif project_filepath.get_extension() in nuke_project_file_extensions:
        return NukeProjectFile(project_filepath)
    else:
        return GenericProjectFile(project_filepath)


def project_files_from_directory(project_directory: 'system.Directory') -> list['GenericProjectFile']:
    """
    Returns a list of GenericProjectFile objects from a directory.
    :param project_directory: Directory to search for project files.
    :return: List of GenericProjectFile objects.
    """
    project_files = []

    for file in project_directory.get_files():
        project_files.append(project_file_from_filepath(file))

    log.info(f"Found {len(project_files)} project files in {project_directory.directory_path}")
    return project_files


