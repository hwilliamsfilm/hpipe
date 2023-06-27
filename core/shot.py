"""
Shot class for the project database. This is the main object for the shot database and can be used to interface
with the file system and database. This class is meant to be used with the project class and not on its own. The reason
for this is that the project class is used to infer certain properties of the shot class such as the base path. Not
using inheritance because shots can be used outside the project class.
"""
from assets import asset, imageSequence, projectFile
import core.constants as constants
from core.hutils import logger, system

from typing import *
if TYPE_CHECKING:
    from core import project

log = logger.setup_logger()
log.debug("shot.py loaded")


class ShotDict(TypedDict):
    shot_name: str
    frame_start: int
    frame_end: int
    project_name: str
    tags: Union[list[str], None]
    user_data: Union[dict[Any, Any], None]


class Shot:
    """
    Base class for a shot in database. This class is meant to be used with the project class and not on its own.
    """

    def __init__(self, shot_name: str, project_instance: 'project.Project', frame_start: int = constants.FRAME_START,
                 frame_end: int = constants.FRAME_END, tags: Union[list[str], None] = None,
                 user_data: Union[dict[Any, Any], None] = None):
        """
        Creates a shot object. Requires a shot name and a project object to connect to. The project is linked to
        the shot object so that various shot properties can be inferred from the project object.
        :param str shot_name: Name of the shot
        :param object project_instance: Project object that the shot belongs to
        :param int frame_start: Starting frame of the shot
        :param int frame_end: Ending frame of the shot
        :param list[str] tags: List of tags for the shot
        :param dict user_data: User data for the shot if any. This can be used to store custom data per shot.
        """

        if not tags:
            tags = []

        if not user_data:
            user_data = {}

        self.name = shot_name
        self.project = project_instance
        self.frame_start = frame_start
        self.frame_end = frame_end
        self.tags = tags
        self.user_data = user_data
        self.base_path = self.get_base_path()

    def __repr__(self):
        return f"Shot <{self.name.upper()}> from project <{self.project.name.upper()}>, " \
               f"frames {self.frame_start} to {self.frame_end}"

    def get_base_path(self) -> str:
        """
        Returns the base path of the shot. This is the path of the project + shots folder.
        :return: str base path
        """

        if not self.project:
            raise ValueError("Project not set for shot")

        return f"{self.project.get_project_path()}/{constants.SHOT_FOLDER}/"

    def get_shot_path(self) -> str:
        """
        Returns the path of the shot
        :return: str shot path
        """
        return f"{self.base_path}/{self.name}"

    def get_plate_path(self) -> 'system.Directory':
        """
        Returns the path of the plate folder
        :return: str plate path
        """
        plate_path = system.Directory(
            f"{self.base_path}/{self.name}/{constants.PLATE_FOLDER}/")
        return plate_path

    def get_workarea_path(self) -> str:
        """
        Returns the path of the workarea folder
        :return: str workarea path
        """
        # return self.get_shot_path() + '/output/' + '_workarea/'
        return f"{self.base_path}/{constants.OUTPUT_FOLDER}/{constants.WORKAREA_FOLDER}/"

    def get_comps_path(self) -> 'system.Directory':
        """
        Returns the path of the comps' folder
        :return: str comps path
        """
        comps_path = system.Directory(
            f"{self.base_path}/{self.name}/{constants.OUTPUT_FOLDER}/{constants.COMP_FOLDER}/")
        return comps_path

    def get_render_path(self):
        """
        Returns the path of the render folder
        :return: str render path
        """
        return f"{self.base_path}/{constants.OUTPUT_FOLDER}/{constants.RENDER_FOLDER}/"

    def get_nuke_path(self):
        """
        Returns the path of the nuke folder
        :return: str nuke scripts path
        """
        nuke_path = system.Directory(
            f"{self.base_path}/{self.name}/{constants.WORKING_FOLDER}/{constants.NUKE_FOLDER}/")
        return nuke_path

    def get_houdini_path(self):
        """
        Returns the path of the houdini folder
        :return: str houdini scripts path
        """
        houdini_path = system.Directory(
            f"{self.base_path}/{self.name}/{constants.WORKING_FOLDER}/{constants.HOUDINI_FOLDER}/")
        return houdini_path

    def get_tags(self) -> list[str]:
        """
        Returns the tags of the shot.
        :return: list[str] tags
        """
        return self.tags

    def get_comps(self) -> list['imageSequence.GenericImageSequence']:
        """
        Get list of comps for the project
        :return: list of comps
        """
        comp_sequences = imageSequence.sequences_from_directory(self.get_comps_path())
        return comp_sequences

    def get_plates(self) -> list['imageSequence.GenericImageSequence']:
        """
        Returns the plates contained in the plate folder.
        :return: list[str] plates
        """
        plate_sequences = imageSequence.sequences_from_directory(self.get_plate_path())
        return plate_sequences

    def get_project_files(self) -> list[projectFile.GenericProjectFile]:
        """
        Returns the project files contained in the nuke and houdini folders.
        :return: list[str] project files
        """
        nuke_path =self.get_nuke_path()
        houdini_path = self.get_houdini_path()
        nuke_files = projectFile.project_files_from_directory(nuke_path)
        houdini_files = projectFile.project_files_from_directory(houdini_path)
        return nuke_files + houdini_files

    def get_renders(self) -> list[str]:
        """
        Returns the renders contained in the render folder.
        :return: list[str] renders
        """
        raise NotImplementedError

    def get_assets(self) -> list[str]:
        """
        Returns the assets contained in the shot.
        :return: list[str] assets
        """
        raise NotImplementedError

    def add_tag(self, tag) -> bool:
        self.tags.append(tag)
        return True

    def remove_all_tags(self) -> bool:
        self.tags = ['']
        return True

    @classmethod
    def from_dict(cls, shot_dictionary: 'ShotDict', parent_project: 'project.Project') -> 'Shot':
        """
        Creates a shot object from a dictionary
        :param shot_dictionary: dict of shot
        :param parent_project: parent project instance
        :return: list of shot objects
        """

        shot_name = shot_dictionary['shot_name']
        frame_start = shot_dictionary['frame_start']
        frame_end = shot_dictionary['frame_end']
        user_data: Union[Dict[Any, Any], None]
        if not shot_dictionary.get('user_data'):
            user_data = {}
        else:
            user_data = shot_dictionary['user_data']

        tags: Union[list[str], None]
        if not shot_dictionary.get('tags'):
            tags = []
        else:
            tags = shot_dictionary['tags']

        shot = cls(shot_name=shot_name, project_instance=parent_project, frame_start=frame_start,
                   frame_end=frame_end, tags=tags, user_data=user_data)
        return shot

    def to_dict(self) -> 'ShotDict':
        """
        Returns the dictionary for the entire shot to be stored along the project in the database
        :return: shot dictionary
        """
        return {
            'shot_name': self.name,
            'frame_start': self.frame_start,
            'frame_end': self.frame_end,
            'project_name': self.project.name,
            'tags': self.tags,
            'user_data': self.user_data,
        }
