from typing import *

from hpipe.assets import asset
from hpipe.core.hutils import logger, system

if TYPE_CHECKING:
    pass

log = logger.setup_logger()
log.debug("projectFile.py loaded")


class GenericProjectFile(asset.Asset):
    """
    Class for a project file. Stores the filepath to the file.
    PROJECT FILE -> ../../../shot_task_desc_version.hiplc
    """
    def __init__(self, filepath: 'system.Filepath', asset_name: str = ''):
        super().__init__(asset_name)
        self.filepath = filepath
        self.asset_type = asset.AssetType.PROJECT_FILE

    def __repr__(self) -> str:
        return f"ProjectFile <{self.filepath}> from " \
               f"<{self.filepath.get_parent_directory()}>"

    def get_filepath(self) -> 'system.Filepath':
        """
        Gets the filepath of the asset.
        :return: Filepath of the asset.
        """
        return self.filepath

    def to_dict(self) -> Dict[str, Any]:
        """
        Converts the asset to a dictionary.
        :return: Dictionary representation of the asset.
        """
        return {
            'asset_name': self.asset_name,
            'filepath': self.filepath.system_path()
        }

    def get_version(self) -> tuple[str, int]:
        """
        Gets the version of the asset.
        assuming that the version if the last number in the filename
        ex. /path/to/file_[A01].hipnc
        :return: Major and minor version of the asset.
        """
        filepath = self.filepath
        version_string = filepath.system_path().split('.')[-2].split('-')[-1]
        version_letter: str = version_string[0]
        version_number: int = int(version_string[1:])
        return version_letter, version_number

    def get_asset_name(self) -> str:
        """
        Gets the name of the current asset.
        """
        filename = self.filepath.get_filename()
        return filename.split('-')[1]

    def get_asset_description(self) -> str:
        """
        Gets the description of the current asset.
        """
        filename = self.filepath.get_filename()
        # log.debug(f"Filename: {filename}")
        if len(filename.split('-')) < 3:
            return None
        return filename.split('-')[2]

    def get_asset_shot(self) -> str:
        """
        Gets the shot of the current asset.
        """
        log.debug(f"Getting shot from project file : {self.filepath}")
        filename = self.filepath.get_filename()
        log.debug(f"Filename: {filename}")
        return filename.split('-')[0]

    def get_asset_project(self) -> str:
        """
        Gets the project of the current asset by looking at the parent directory.
        """
        filepath = self.filepath
        directory_list = filepath.system_path().split('/')
        project_index = directory_list.index('projects')
        project = directory_list[project_index + 2]
        return project

    @classmethod
    def from_dict(cls, asset_dict: Dict[Any, Any]) -> Union[None, Any]:
        """
        Converts a dictionary to an asset.
        :param asset_dict: Dictionary to convert.
        :return: None
        """
        file_path = system.Filepath(asset_dict['filepath'])
        asset_name = asset_dict['asset_name']
        return cls(file_path, asset_name)


class HoudiniProjectFile(GenericProjectFile):
    """
    Class for a Houdini project file. Stores the filepath to the file.
    """
    def __init__(self, filepath: 'system.Filepath', asset_name: str = ''):
        super().__init__(filepath, asset_name)

    def __repr__(self) -> str:
        return f"HoudiniProjectFile <{self.filepath}> from " \
               f"<{self.filepath.get_parent_directory()}>"

    def to_dict(self) -> Dict[str, Any]:
        """
        Converts the asset to a dictionary.
        :return: Dictionary representation of the asset.
        """
        return {
            'asset_name': self.asset_name,
            'filepath': self.filepath.system_path()
        }


class NukeProjectFile(GenericProjectFile):
    """
    Class for a Nuke project file. Stores the filepath to the file.
    """
    def __init__(self, filepath: 'system.Filepath', asset_name: str = ''):
        super().__init__(filepath, asset_name)

    def __repr__(self) -> str:
        return f"NukeProjectFile <{self.filepath}> from " \
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


def project_files_from_directory(project_directory: 'system.Directory') -> List['GenericProjectFile']:
    """
    Returns a list of GenericProjectFile objects from a directory.
    :param project_directory: Directory to search for project files.
    :return: List of GenericProjectFile objects.
    """
    project_files = []

    log.debug(f"Searching for project files in {project_directory}")

    if not isinstance(project_directory, system.Directory):
        log.error(f"project_directory is not a system.Directory object. "
                  f"Got {type(project_directory)} instead.")
        return project_files

    for file in project_directory.get_files():
        project_files.append(project_file_from_filepath(file))

    log.info(f"Found {len(project_files)} project files in {project_directory.directory_path}")
    return project_files


