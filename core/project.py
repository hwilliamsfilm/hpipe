"""
Project class for the project database. This is the main object for the project database and can be used to interface
with the file system and database.
"""

from core.hutils import logger, manager_utils
from core import shot
from assets import asset, imageSequence
import core.constants as constants
from typing import *

import datetime
import os

log = logger.setup_logger()
log.debug("project.py loaded")


class ProjectDict(TypedDict):
    project_name: str
    date_created: str
    description: str
    member_shots: Union[Dict[str, Any], None]
    user_data: Union[Dict[Any, Any], None]


class Project:
    """
    Class representing a Project in the Project Database
    """

    def __init__(self, project_name: str, date_created: str = '', description: str = '',
                 member_shots: Union[Dict[str, Any], None] = None, user_data: Union[Dict[Any, Any], None] = None):
        """
        Creates a project object. This is the main object for the project database and can be used to interface with
        the file system and database.
        :param str project_name: Name of the project
        :param str date_created: Date the project was created
        :param str description: Description of the project
        :param list member_shots: List of shots in the project
        :param dict user_data: User data for the project if any. This can be used to store custom data per shot
        """
        self.name = project_name
        self.description = description

        if not date_created:
            date_created = str(datetime.date.today())

        self.year = date_created.split('-')[0]
        self.date = date_created

        if not member_shots:
            member_shots = {}

        self.shots = manager_utils.shots_from_dict(member_shots, self)
        self.user_data = user_data

    def __repr__(self):
        return f"Project <{self.name.upper()}> {self.description}, created on {self.date}, " \
               f"with {len(self.shots)} shots."

    def get_shots(self) -> list[shot.Shot]:
        """
        Returns the list of shots in the project.
        :return: list of shots if they exist
        """
        return self.shots

    def get_shot(self, shot_name: str = '') -> shot.Shot:
        """
        Returns a shot object from the project
        :param str shot_name: Name of the shot
        :return: Shot object
        """
        return [s for s in self.shots if s.name == shot_name][0]

    def get_project_path(self) -> str:
        """
        Get file server path for project directory using constants
        :return: str path
        """
        return f"{constants.PROJECTS_ROOT}/{self.year}/{self.name}"

    def get_archive_path(self) -> str:
        """
        Get path for project directory using constants
        :return: str path
        """
        return f"{constants.ARCHIVE_ROOT}/{self.year}/{self.name}"

    def get_assets_path(self) -> str:
        """
        Get path for project directory using constants
        :return: str path
        """
        return f"{self.get_project_path()}/_assets/"

    def get_comps_path(self) -> str:
        """
        Get path for project directory using constants
        :return: str path
        """
        return f"{self.get_project_path()}/comps/"

    def get_delivery_path(self) -> str:
        """
        Get path for project directory using constants
        :return: str path
        """
        return f"{self.get_project_path()}/deliveries/"

    def get_shot_path(self) -> str:
        """
        Get path for shot directory for project using constants. Checks for the old file structure first
        :return:
        """
        shot_path = f'{self.get_project_path()}/shots/'

        if not os.path.exists(shot_path):

            # Check for deprecated file structure
            shot_path = f'{self.get_project_path()}/scenes/'
            if not os.path.exists(shot_path):

                # should not happen
                raise FileNotFoundError(f"Could not find shots or scenes directory for {self.name}")

        return shot_path

    def create_shot(self, shot_name: str, frame_start: int = 1001, frame_end: int = 1100,
                    user_data: Union[Dict[Any, Any], None] = None, tags: Union[List[Any], None] = None) -> shot.Shot:
        """
        Creates a shot object and adds it to the project
        :param str shot_name: Name of the shot
        :param int frame_start: Start frame of the shot
        :param int frame_end: End frame of the shot
        :param dict user_data: User data for the shot if any. This can be used to store custom data per shot
        :param list tags: List of tags for the shot
        :return: Shot object
        """

        if not user_data:
            user_data = {}

        if not tags:
            tags = []

        new_shot = shot.Shot(shot_name, project_instance=self, frame_start=frame_start, frame_end=frame_end,
                             user_data=user_data, tags=tags)
        self.shots.append(new_shot)
        return new_shot

    def export_shots(self) -> dict:
        """
        Export the shots in the project to a dictionary for storage in the database.
        :return: dict of shots
        """

        shot_dictionary = {}
        for shot_instance in self.get_shots():
            shot_dictionary[shot_instance.name] = shot_instance.to_dict()
        return shot_dictionary

    @classmethod
    def from_dict(cls, project_dictionary: ProjectDict) -> 'Project':
        """
        Creates a project object from a json string. Currently, this is used for DB to create the project objects
        :returns: Project object from project dictionary
        """
        project_name = project_dictionary['project_name']
        date_created = project_dictionary['date_created']
        description = project_dictionary['description']
        shots = project_dictionary['member_shots']
        user_data: Union[Dict[Any, Any], None]
        if not project_dictionary.get('user_data'):
            user_data = {}
        else:
            user_data = project_dictionary['user_data']

        project = cls(project_name, date_created, description, shots, user_data)
        return project

    def to_dict(self) -> 'ProjectDict':
        """
        Returns the dictionary for the entire project to be stored in db.
        :return:
        """
        project_name = self.name
        date_created = self.date
        description = self.description
        shots = self.export_shots()
        user_data = self.user_data
        return {
            'project_name': project_name,
            'member_shots': shots,
            'date_created': date_created,
            'description': description,
            'user_data': user_data
        }
