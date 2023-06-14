'''
Project class for active shots
'''

import core.constants as constants
from core.hutils import logger
from core.hutils import path
import os

# log module import
logger.imported("shot.py")

class Shot:
    """
    Base class for a shot in database.
    """

    def __init__(self,
                 shot_name,
                 project,
                 frame_start=constants.FRAME_START,
                 frame_end=constants.FRAME_END,
                 tags=None):
        """
        Creates a shot object. Requires a shot name and a project object to connect to. The project is linked to
        the shot object so that various shot properties can be inferred from the project object.

        :param shot_name: str name of shot
        :param project: object of project
        :param frame_start: int start frame
        :param frame_end: int end frame
        :param tags: list of tags
        """

        self.name = shot_name
        self.project = project
        self.frame_start = frame_start
        self.frame_end = frame_end
        self.tags = tags

        # need to get base path from the project object (self.project)
        self.base_path = self.get_base_path()

    def __repr__(self):
        return '<Shot {name}>'.format(name=self.name)

    @classmethod
    def from_json(cls, dict, proj=None):
        # NOTE: This may or may not be used in the future since shots can only be created from a project object
        """
        Creates a shot from a json string
        :returns: Shot object from json string
        """

        if dict.get('project'):
            project = dict.get('project')
        elif dict.get('proj'):
            project = dict.get('proj')

        return cls(dict.get('name'), project=project, frame_start=dict.get('fstart'),
                   frame_end=dict.get('fend'), tags=dict.get('tags'))

    # Getting path things

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

    def tag_string(self):
        return self.tags

    def remove_all_tags(self):
        self.tags = ''
        return

    def export(self):
        """
        Returns the dictionary for the entire shot to be stored along the project in the database
        :return: shot dictionary
        """

        logger.debug('Exporting shot {0}...'.format(self.name))

        return {
            'name': self.name,
            'fstart': self.frame_start,
            'fend': self.frame_end,
            'project': self.project,
            'tags': self.tag_string()
        }
