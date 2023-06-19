'''
Project class for active projects
'''

from core.hutils import logger, errors, directory
from core import shot
import core.constants as constants

import os
from importlib import reload
import datetime

# log module import
# logger.imported("project.py")

def _shots_from_dict(shot_dictionary, project):
    """
    Creates a list of shot objects from a dictionary. Extracting this from the project class to
    create shot objects with references to the project class. Could be used outside of this class.
    :param shots: dict of shots
    :return: list of shot objects
    """

    shots = []
    if shot_dictionary:
        for shot_name, shot_dict in shot_dictionary.items():
            frame_start = shot_dict.get('fstart')
            frame_end = shot_dict.get('fend')
            tags = shot_dict.get('tags')
            shot_object = shot.Shot(shot_name=shot_name, project=project, frame_start=frame_start,
                                    frame_end=frame_end, tags=tags)

            shots.append(shot_object)

    return shots



class Project:
    """
    Class representing a Project in the Project Database
    """

    def __init__(self, name, client='self', date=None, description=None, shots=None):
        """
        Creates a project object
        :param name: Name of the project
        :param client: Name of the client, mostly "self"
        :param date: Date of creation if it exists
        :param description: Brief description of the project for remembering 20 yrs from now
        :param shots: Shots in the project
        """
        self.name = name
        self.client = client
        self.description = description

        # create date if not specified
        if not date:
            date = str(datetime.date.today())
        self.year = date.split('-')[0]
        self.date = date


        self.shots = _shots_from_dict(shots, self)

    def __repr__(self):
        return '<Project {name}>'.format(name=self.name)

    @classmethod
    def from_json(cls, project_dictionary):
        """
        Creates a project object from a json string. Currently used for DB to create the project objects
        :returns: Project object from project dictionary
        """

        # check if there are shots and if so, create them
        # if project_dictionary.get('shots'):
        #     for shot in project_dictionary.get('shots'):
        #         shot_name = shot.get('name')
        #         #project = # i want a reference to the project being built here
        #
        #     shots = [shot.Shot.from_json(v) for k, v in project_dictionary.get('shots').items()]

        # create project from dictionary
        project = cls(project_dictionary.get('name'), client=project_dictionary.get('client'),
                      date=project_dictionary.get('date'), description=project_dictionary.get('descript'),
                      shots=project_dictionary.get('shots'))

        return project

    # Getting object things
    def get_shots(self):
        """
        Returns a list of shots
        :return: list of shots if they exist
        """
        return self.shots

    def get_shot(self, shot_name):
        """
        Returns a shot object from the project
        :param str shot_name: Name of the shot
        :return: Shot object
        """
        return [s for s in self.shots if s.name == shot_name][0]

    # Getting path things
    def get_project_path(self):
        """
        Get path for project directory using constants
        :return: str path
        """
        return '{root}/{year}/{name}'.format(root=constants.PROJECTS_ROOT, year=self.year, name=self.name)

    def get_archive_path(self):
        """
        Get path for project directory using constants
        :return: str path
        """
        return '{root}/{year}/{name}'.format(root=constants.ARCHIVE_ROOT, year=self.year, name=self.name)

    def get_assets_path(self):
        """
        Get path for project directory using constants
        :return: str path
        """
        return '{0}/_assets/'.format(self.get_project_path())

    def get_comps_path(self):
        """
        Get path for project directory using constants
        :return: str path
        """
        return '{0}/comps/'.format(self.get_project_path())

    def get_delivery_path(self):
        """
        Get path for project directory using constants
        :return: str path
        """
        return '{0}/deliveries/'.format(self.get_project_path())

    def get_shot_path(self):
        """
        Get path for shot directory for project using constants. Checks for the old file structure first
        :return:
        """
        path = self.get_project_path()
        shot_path = '{0}/shots/'.format(path)

        # Need to check if project was the old file structure
        if not os.path.exists(shot_path):
            shot_path = '{0}/scenes/'.format(path)
            if not os.path.exists(shot_path):
                return None

        return shot_path

    # Doing things
    def create_shot(self, name, frame_start=constants.FRAME_START, frame_end=constants.FRAME_END):
        """
        Adds shot to current project
        :return:
        """
        new_shot = shot.Shot(name, frame_start=frame_start, frame_end=frame_end, proj=self.name)
        self.shots.append(new_shot)
        return new_shot

    # Exporting Things
    def export_shots(self):
        """
        export shots for storage in db
        :return: dict of shots
        """

        shot_dictionary = {}
        for shot in self.get_shots():
            shot_dictionary[shot.name] = shot.export()
        return shot_dictionary

    def export_project(self):
        """
        Returns the dictionary for the entire project to be stored in db
        :return:
        """

        return {
            'name': self.name,
            'shots': self.export_shots(),
            'client': self.client,
            'date': self.date,
            'descript': self.description
        }