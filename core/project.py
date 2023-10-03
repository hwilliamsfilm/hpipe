"""
Project class for the project database. This is the main object for the project database and can be used to interface
with the file system and database.
"""

import datetime
import os
from typing import *

import core.constants as constants
from core import shot
from core.hutils import logger, manager_utils
import sys

if sys.version_info <= (3, 8):
    from typing_extensions import TypedDict, Literal, overload

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

    def get_shots(self) -> List[shot.Shot]:
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

    def create_project_USD(self):
        """
        Creates a project-level USD file that will be referenced by all the shots in the project.
        """
        raise NotImplementedError

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

    def add_shot(self, shot_instance: shot.Shot) -> bool:
        """
        Adds a shot to the project.
        :param shot.Shot shot_instance: shot instance to be added to the project
        :returns: True if successful.
        """
        if shot_instance.name in [s.name for s in self.get_shots()]:
            log.warning(f"Shot {shot_instance.name} already exists in project {self.name}")
            return False

        self.shots.append(shot_instance)
        return True

    def remove_shot(self, shot_name: str) -> bool:
        """
        Removes shot from shot list.
        :param shot_name: shot name to be removed.
        :returns: True if successful.
        """
        if not self.get_shot(shot_name):
            log.warning('Shot to remove does not exist.')
            return False

        shot_amount = len(self.shots)

        new_shot_list = []
        for shot_instance in self.shots:
            if shot_instance.name == shot_name:
                continue
            new_shot_list.append(shot_instance)
        self.shots = new_shot_list

        if len(self.shots) != shot_amount-1:
            raise Exception

        return True

    def update_shot(self, shot_to_update: shot.Shot) -> bool:
        """
        Updates a project in the database given a project instance. This is the primary method for updating a project.
        :param project.Project shot_to_update: project instance to be updated in the database
        :returns: True if successful.
        """
        shot_name = shot_to_update.name

        if shot_name not in [s.name for s in self.get_shots()]:
            log.warning(f"Project {shot_name} not found in database in project {self.name}")
            return False

        self.remove_shot(shot_name)
        self.shots.append(shot_to_update)

        return True

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
