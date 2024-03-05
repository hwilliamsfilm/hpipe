from collections import OrderedDict
from hpipe.core import data_manager, project, shot
import sys
try:
    import hou
    from PySide2 import QtWidgets, QtGui
except Exception as e:
    print(f'hou not found, not running in houdini: {e}')
    from PySide6 import QtWidgets, QtGui

from hpipe.core.hutils import logger
from enum import Enum
from hpipe.core.hutils import system
from hpipe.core import data_manager
from typing import *
from hpipe.assets import reviewable
from hpipe.core import assetEntry

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
        "Ref": system.Filepath(r"Y:\projects\2023\{show}\shots\{shot}\ref"),
        "Assets": system.Filepath(r"Y:\projects\2023\{show}\shots\{shot}\ref"),
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


def get_reviewables(shot_list: Optional[List[shot.Shot]], type: str, filter: str) -> Optional[List[reviewable.Reviewable]]:
    """
    Get a list of output directories for a given project, shot and type.
    :param shot: List[shot.Shot]
    :param type: string output type
    :return: List of reviewables or None
    """
    log.debug(f"Getting reviewables for {shot_list}")
    if not shot_list:
        return None

    asset_db = data_manager.AssetDataManager()

    reviewables = []
    for shot in shot_list:
        if type == 'Comp':
            reviewables += shot.get_comps()
        elif type == 'Plate':
            plates = shot.get_plates()
            for plate in plates:
                name = plate.asset_name
                log.debug(f"Plate name: {name}")
                if 'ref' in name.lower():
                    reviewables.append(plate)
    if type == 'Assets':
        asset_reviewables = assetEntry.reviewable_factory(asset_db.get_assets())
        reviewables += asset_reviewables

    filtered_reviewables = []
    if filter and filter != '':
        for reviewable in reviewables:
            if filter in reviewable.asset_name.lower():
                filtered_reviewables.append(reviewable)
        log.debug(f"Filtered reviewables: {filtered_reviewables}")
        return filtered_reviewables
    log.debug(f"Reviewables: {reviewables}")
    return reviewables


