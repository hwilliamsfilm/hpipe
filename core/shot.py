"""
Shot class for the project database. This is the main object for the shot database and can be used to interface
with the file system and database. This class is meant to be used with the project class and not on its own. The reason
for this is that the project class is used to infer certain properties of the shot class such as the base path. Not
using inheritance because shots can be used outside the project class.
"""

import core.constants as constants
from core.hutils import logger

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

    def get_plate_path(self) -> str:
        """
        Returns the path of the plate folder
        :return: str plate path
        """
        # return self.get_shot_path() + '/plate/'
        return f"{self.base_path}/{constants.PLATE_FOLDER}/"

    def get_workarea_path(self) -> str:
        """
        Returns the path of the workarea folder
        :return: str workarea path
        """
        # return self.get_shot_path() + '/output/' + '_workarea/'
        return f"{self.base_path}/{constants.OUTPUT_FOLDER}/{constants.WORKAREA_FOLDER}/"

    def get_comps_path(self) -> str:
        """
        Returns the path of the comps' folder
        :return: str comps path
        """
        return f"{self.base_path}/{constants.OUTPUT_FOLDER}/{constants.COMP_FOLDER}/"

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
        # return self.get_shot_path() + '/working_files/' + 'nuke/'
        return f"{self.base_path}/{constants.WORKING_FOLDER}/{constants.NUKE_FOLDER}/"

    def get_houdini_path(self):
        """
        Returns the path of the houdini folder
        :return: str houdini scripts path
        """
        return self.get_shot_path() + '/working_files/' + 'houdini/'

    def get_tags(self) -> list[str]:
        """
        Returns the tags of the shot.
        :return: list[str] tags
        """
        return self.tags

    def get_comps(self) -> list[str]:
        """
        Returns the comps contained in the comps' folder
        :return: list[str] comps
        """
        # FIXME: Need to use factory pattern to return image sequence objects
        raise NotImplementedError

    def get_plates(self) -> list[str]:
        """
        Returns the plates contained in the plate folder.
        :return: list[str] plates
        """
        # FIXME: Need to use factory pattern to return image sequence objects
        raise NotImplementedError

    def get_work(self) -> list[str]:
        """
        Returns the work contained in the workarea folder.
        :return: list[str] work
        """
        # FIXME: Need to use factory pattern to return image sequence objects. Also not clear what "work" is.
        # dir = self.get_workarea_path()
        # return path.get_image_dirs(dir)
        raise NotImplementedError

    def get_project_files(self) -> list[str]:
        """
        Returns the project files contained in the nuke and houdini folders.
        :return: list[str] project files
        """
        # FIXME: Need to use factory pattern to general ProjectFile objects
        # return nuke_files + houdini_files
        raise NotImplementedError

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

    def link_project(self, project_instance: 'project.Project') -> bool:
        # FIXME: I should probably not support this.
        self.project = project_instance
        return True

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
        tags = shot_dictionary['tags']
        user_data = shot_dictionary['user_data']

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
