
from collections import OrderedDict
from core import data_manager, project
import datetime
from PySide6 import QtWidgets
from PySide6 import QtGui


class Constants():
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


def get_db_data():
    """
    Get data from json file
    :return:
    """
    database = data_manager.ProjectDataManager().data

    return database


def save_db_data(data):
    """
    Save data to json file
    :param data:
    :return:
    """
    raise NotImplementedError


def add_project(project_name):
    """
    Add a project to the json file
    :param data:
    :param project_name:
    :return:
    """
    # get date
    date = datetime.datetime.now().strftime('%Y-%m-%d')

    # create project object
    proj = project.Project(project_name, date=date)

    # add project to data
    data_manager.ProjectDataManager().add_project(proj)

    return True


def add_shot(project_name, shot_name):
    """
    Add a shot to the json file
    :param data:
    :param project_name:
    :param shot_name:
    :return:
    """

    raise NotImplementedError


def remove_shot(project_name, shot_name):
    """
    Remove a shot from the json file
    :param data:
    :param project_name:
    :param shot_name:
    :return:
    """
    raise NotImplementedError


def remove_project(project_name):
    """
    Remove a project from the json file
    :param data:
    :param project_name:
    :return:
    """
    raise NotImplementedError


def add_shot_tags(project_name, shot_name, tags):
    """
    Add tags to a shot
    :param project_name:
    :param shot_name:
    :param tags:
    :return:
    """
    raise NotImplementedError


def remove_shot_tags(project_name, shot_name):
    """
    Remove tags from a shot
    :param project_name:
    :param shot_name:
    :param tags:
    :return:
    """
    raise NotImplementedError


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
