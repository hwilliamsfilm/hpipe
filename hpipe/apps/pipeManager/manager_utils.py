
from collections import OrderedDict

from hpipe.core import data_manager, project, shot
import sys
if sys.version_info <= (3, 8):
    from PySide2 import QtWidgets, QtGui
else:
    from PySide6 import QtWidgets, QtGui
from hpipe.core.hutils import logger
from enum import Enum
from typing import *

log = logger.setup_logger()
log.debug("manager_utils.py loaded")


class TargetLocationType(Enum):
    """
    Enum class that represents the type of target location. Global means that it could be
    stored at the global, project, or shot level. Project can only be stored at the project
    and shot level, etc.
    """
    GLOBAL = 0
    PROJECT = 1
    SHOT = 2


class Constants:
    """
    Constants for the project overview
    """
    TAGS = {
        "ingested": {"color": "#0000FF", "text_color": "black"},
        "tracked": {"color": "#FFA500", "text_color": "black"},
        "first look": {"color": "#00FF00", "text_color": "black"},
        "final": {"color": "#FF0000", "text_color": "black"},
        "delivered": {"color": "#000000", "text_color": "white"},
        "maybe": {"color": "#000000", "text_color": "white"},
        "other": {"color": "#ADD8E6", "text_color": "black"},
        "ACTIVE": {"color": "#00FF00", "text_color": "black"},
    }
    SORTING_TYPES = ['Project Name A-Z', 'Project Name Z-A', 'Date Created Newest', 'Date Created Oldest']
    INGEST_LOCATIONS = ['Asset', 'Trak', 'Plate', 'Delivery']


def ingest_file(filepath: str, target_location: str, project_object: Union[project.Project, None],
                shot_object: Union[shot.Shot, None]) -> bool:
    """
    Ingests a file into the database. This means that it will be copied to the appropriate location
    and a database entry will be created for it.
    :param filepath: filepath of the file to ingest
    :param target_location: target location to ingest the file to
    :param project_object: project object to ingest the file to
    :param shot_object: shot object to ingest the file to
    :return: True if successful, False if not
    """
    from core.hutils import system
    from hpipe.core import constants
    dropped_item = system.path_factory(filepath)

    if not dropped_item.exists():
        log.warning(f'File or directory {filepath} does not exist. Cannot ingest.')
        return False

    # TODO: make location path a directory object
    location_path = constants.GLOBAL_ASSETS
    
    if target_location == 'Asset':
        location_path = constants.GLOBAL_ASSETS
        if project_object:
            location_path = project_object.get_assets_path()
    if target_location == 'Plate':
        location_path = constants.GLOBAL_PLATES # TODO: add to constants
        if project_object:
            if shot_object:
                location_path = shot_object.get_plate_path()

    return True


def parse_data(manager: data_manager.ProjectDataManager) -> dict:
    """
    Parse data from data manager. Returns data but in a reader friendly format.
    """
    display_data = {}

    for project_instance in manager.get_projects():
        project_name = project_instance.name.replace("_", " ").lower()
        project_display_data = {
            'Shots:': {},
            'Description:': project_instance.description,
            'Date:': project_instance.date
        }
        for shot_instance in project_instance.get_shots():
            shot_display_data = {'Start Frame:': shot_instance.frame_start,
                                 'End Frame:': shot_instance.frame_end,
                                 'Tags:': shot_instance.get_tags(),
                                 'User Data:': shot_instance.user_data}
            shot_name = shot_instance.name
            project_display_data['Shots:'][shot_name] = shot_display_data
        display_data[project_name] = project_display_data
    return display_data


def encode_data(tree_dictionary: dict, database: data_manager.ProjectDataManager) -> dict:
    """
    Encodes the tree data into database format. Compares against the current DB data.
    :param tree_dictionary: dictionary to encode into a dictionary compatible with the database.
    :param database: data manager to compare against
    :returns: encoded dictionary
    """

    dictionary_a = database.data.copy()

    for key, value in tree_dictionary.items():
        project_name = key.replace(" ", "_").lower()
        db_project = database.get_project(project_name)
        # db_project.date = tree_dictionary[key]['Date:']
        db_project.description = tree_dictionary[key]['Description:']
        for shot_name in tree_dictionary[key]['Shots:']:
            db_shot = db_project.get_shot(shot_name)
            db_shot.user_data = tree_dictionary[key]['Shots:'][db_shot.name]['User Data:']
            db_shot.tags = tree_dictionary[key]['Shots:'][db_shot.name]['Tags:']
            db_shot.frame_start = tree_dictionary[key]['Shots:'][db_shot.name]['Start Frame:']
            db_shot.frame_end = tree_dictionary[key]['Shots:'][db_shot.name]['End Frame:']
            db_project.update_shot(db_shot)
        database.update_project(db_project, push=False)

    dictionary_b = database.data.copy()
    compare_data(dictionary_b, dictionary_a)
    return database.data


def sort_data(data: dict, sorting_type: str) -> dict:
    """
    Sort data by project name
    """
    if sorting_type == 'Project Name A-Z':
        sorted_data = OrderedDict(sorted(data.items(), key=lambda x: x[0]))
    elif sorting_type == 'Project Name Z-A':
        sorted_data = OrderedDict(sorted(data.items(), key=lambda x: x[0], reverse=True))
    elif sorting_type == 'Date Created Newest':
        sorted_data = OrderedDict(sorted(data.items(), key=lambda x: x[1]['Date:'], reverse=True))
    elif sorting_type == 'Date Created Oldest':
        sorted_data = OrderedDict(sorted(data.items(), key=lambda x: x[1]['Date:']))
    else:
        sorted_data = data

    # remove date from sorted data
    for key, value in sorted_data.items():
        value.pop('Date:', None)

    return sorted_data


def compare_data(dictionary_a: dict, dictionary_b: dict, path: str = '') -> None:
    """
    Compares two dictionaries and prints out the differences to the log. If a key is not in the ground truth dictionary
    it will be printed out as a warning.
    :param dictionary_a: New dictionary to compare
    :param dictionary_b: Ground truth dictionary to compare against
    :param path: Path to the dictionary
    :return: dict of differences
    """

    for k in dictionary_a:
        if k in dictionary_b:
            if type(dictionary_a[k]) is dict:
                compare_data(dictionary_a[k], dictionary_b[k], "[%s/%s]" % (path, k) if path else k)
                continue
            if str(dictionary_a[k]) != str(dictionary_b[k]):
                result = ["%s: " % path, " DB %s : %s -->" % (k, dictionary_b[k]), " TXT %s : %s" % (k, dictionary_a[k])]
                log.debug(" ".join(result))
        else:
            log.info("%s%s as key not in DB\n" % ("%s: " % path if path else "", k))


def get_db_data():
    """
    Get data from json file
    :return:
    """
    database = data_manager.ProjectDataManager().data

    return database


def create_tag_button(tag):
    button = QtWidgets.QPushButton(tag)
    if tag in Constants.TAGS:
        button.setStyleSheet("border-radius: 5px; "
                             "background-color: %s; "
                             "color: %s" % (Constants.TAGS[tag]["color"], Constants.TAGS[tag]["text_color"]))
    else:
        button.setStyleSheet("border-radius: 5px; "
                             "background-color: %s; "
                             "color: %s" % (Constants.TAGS["other"]["color"], Constants.TAGS["other"]["text_color"]))
    button.setFixedWidth(80)
    button.setFixedHeight(30)
    button.setFont(QtGui.QFont("Arial", 8, QtGui.QFont.Bold))
    return button
