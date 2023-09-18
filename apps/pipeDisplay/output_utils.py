from collections import OrderedDict
from core import data_manager, project, shot
import sys
if sys.version_info <= (3, 8):
    from PySide2 import QtWidgets, QtGui
else:
    from PySide6 import QtWidgets, QtGui
from core.hutils import logger
from enum import Enum
from core.hutils import system
from core import data_manager
from typing import *
from assets import reviewable

log = logger.setup_logger()
log.debug("manager_utils.py loaded")


class Constants:
    """
    Constants for the project overview
    """
    DIRECTORY_TYPES = {
        "Comp": system.Filepath(r"Y:\projects\2023\{show}\shots\{shot}\output\comp"),
        "Plate": system.Filepath(r"Y:\projects\2023\{show}\shots\{shot}\plate"),
        "Workarea": system.Filepath(r"Y:\projects\2023\{show}\shots\{shot}\output\_workarea"),
        "Renders": system.Filepath(r"Y:\projects\2023\{show}\shots\{shot}\output\render"),
        "Ref": system.Filepath(r"Y:\projects\2023\{show}\shots\{shot}\ref")
    }
    SHOWS = data_manager.ProjectDataManager().get_project_names()
    START_PROJECT = "defaults"
    TEMP_IMAGE = system.Filepath(r'Y:\_houdini_\icons\main.png')


def shots_from_show(show: str, database: Optional[data_manager.ProjectDataManager] = None) -> List[str]:
    """
    Get a list of shots from a show
    :param show: str
    :return: List[str]
    """
    if not database:
        database = data_manager.ProjectDataManager()
    project = database.get_project(show)
    shots = [shot.name for shot in project.get_shots()]
    return shots


def get_reviewables(shot_list: Optional[List[shot.Shot]], type: str) -> Optional[List[reviewable.Reviewable]]:
    """
    Get a list of output directories for a given project, shot and type.
    :param shot: List[shot.Shot]
    :param type: string output type
    :return: List of reviewables or None
    """
    log.debug(f"Getting reviewables for {shot_list}")
    if not shot_list:
        return None

    reviewables = []
    for shot in shot_list:
        if type == 'Comp':
            reviewables += shot.get_comps()
        elif type == 'Plate':
            reviewables += shot.get_plates()

    return reviewables


