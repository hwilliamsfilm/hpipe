"""
Shot class for the project database. This is the main object for the shot database and can be used to interface
with the file system and database. This class is meant to be used with the project class and not on its own. The reason
for this is that the project class is used to infer certain properties of the shot class such as the base path. Not
using inheritance because shots can be used outside the project class.
"""

import core.constants as constants
from core.hutils import logger, path
import os

from typing import *
if TYPE_CHECKING:
    from core import project

log = logger.setup_logger()
log.debug("shot.py loaded")


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
        return '<Shot {name}>'.format(name=self.name)

    def get_base_path(self):
        """
        Returns the base path of the shot
        :return: str base path
        """
        return self.project.get_project_path() + '/shots/'


    def get_shot_path(self):
        """
        Returns the path of the shot
        :return: str shot path
        """
        return self.base_path + self.name

    def get_plate_path(self):
        """
        Returns the path of the plate folder
        :return: str plate path
        """
        return self.get_shot_path() + '/plate/'

    def get_workarea_path(self):
        """
        Returns the path of the workarea folder
        :return: str workarea path
        """
        return self.get_shot_path() + '/output/' + '_workarea/'

    def get_comps_path(self):
        """
        Returns the path of the comps folder
        :return: str comps path
        """
        return self.get_shot_path() + '/output/' + 'comp/'

    def get_render_path(self):
        """
        Returns the path of the render folder
        :return: str render path
        """
        return self.get_shot_path() + '/output/' + 'render/'

    def get_nuke_path(self):
        """
        Returns the path of the nuke folder
        :return: str nuke scripts path
        """
        return self.get_shot_path() + '/working_files/' + 'nuke/'

    def get_houdini_path(self):
        """
        Returns the path of the houdini folder
        :return: str houdini scripts path
        """
        return self.get_shot_path() + '/working_files/' + 'houdini/'

    def get_tags(self):
        """
        Returns the tags of the shot. Tags are comma separated strings, and are returned as a list. The tags
        are used to mark shot milestones for production tracking.
        :return:
        """
        if self.tags is not None:
            return self.tags.split(',')
        else:
            return []

    # Getting shot things
    def get_comps(self):
        dir = self.get_comps_path()
        try:
            return path.get_image_dirs(dir)
        except Exception as e:
            logger.error('Error getting comps for shot {0}: {1}'.format(self.name, e))
            return []

    def get_plates(self, database=None):
        plate_dir = self.get_plate_path(database=database)
        try:
            return path.get_image_dirs(plate_dir)
        except Exception as e:
            logger.error('Error getting plates for shot {0}: {1}'.format(self.name, e))
            return []

    def get_work(self):
        dir = self.get_workarea_path()
        return path.get_image_dirs(dir)

    def get_project_files(self):
        from assets import projectFile
        from assets import projectFile
        from pprint import pprint
        nuke_files = [projectFile.NukeProjectFile(os.path.join(self.get_nuke_path(), s)) for s in os.listdir(self.get_nuke_path()) if '.nk' in s and '~' not in s and 'autosave' not in s]
        houdini_files = [projectFile.HoudiniProjectFile(os.path.join(self.get_houdini_path(), s)) for s in os.listdir(self.get_houdini_path()) if '.hiplc' in s]

        return nuke_files + houdini_files

    def get_renders(self):
        rpath = self.get_render_path()
        return path.get_image_dirs(rpath)

    def get_assets(self):
        return NotImplementedError

    # Doing Shot things
    def link_project(self, proj):
        self.project = proj

    def add_tag(self, tag):
        current_tags = self.tags

        logger.warning('Current tags: {0}'.format(current_tags))
        logger.warning('Adding tag: {0}'.format(tag))

        if current_tags is None:
            self.tags = tag
        else:
            self.tags = current_tags + ',' + tag

    def remove_all_tags(self) -> bool:
        self.tags = ''
        return True

    @classmethod
    def from_dict(cls, shot_dictionary: dict, parent_project: object) -> 'Shot':
        """
        Creates a shot object from a dictionary
        :param shot_dictionary: dict of shot
        :param parent_project: parent project instance
        :return: list of shot objects
        """
        shot_name = shot_dictionary.get('name')
        frame_start = shot_dictionary.get('frame_start') or shot_dictionary.get('fstart')
        frame_end = shot_dictionary.get('frame_end') or shot_dictionary.get('fend')
        tags = shot_dictionary.get('tags')
        user_data = shot_dictionary.get('user_data')

        shot = cls(shot_name, parent_project, frame_start, frame_end, tags, user_data)
        return shot

    def to_dict(self) -> dict:
        """
        Returns the dictionary for the entire shot to be stored along the project in the database
        :return: shot dictionary
        """
        return {
            'name': self.name,
            'frame_start': self.frame_start,
            'frame_end': self.frame_end,
            'project': self.project.name,
            'tags': self.tag_string()
        }


