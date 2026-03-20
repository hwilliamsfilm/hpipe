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
    DIRECTORY_TYPES = OrderedDict([
        ("Comp", system.Filepath(r"Y:\projects\2023\{show}\shots\{shot}\output\comp")),
        ("Plate", system.Filepath(r"Y:\projects\2023\{show}\shots\{shot}\plate")),
        ("Renders", system.Filepath(r"Y:\projects\2023\{show}\shots\{shot}\output\render")),
        ("Workarea", system.Filepath(r"Y:\projects\2023\{show}\shots\{shot}\output\_workarea")),
        ("Project Files", system.Filepath(r"Y:\projects\2023\{show}\shots\{shot}\working")),
        ("Ref", system.Filepath(r"Y:\projects\2023\{show}\shots\{shot}\ref")),
        ("Assets", system.Filepath(r"Y:\projects\2023\{show}\shots\{shot}\ref")),
    ])
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


def get_reviewables(shot_list: Optional[List[shot.Shot]], type: str, filter: str,
                    warnings_out: Optional[List[str]] = None) -> Optional[List[reviewable.Reviewable]]:
    """
    Get a list of reviewables for a given project, shot list, and output type.

    Supports: Comp, Plate, Renders, Workarea, Ref, Project Files, Assets.

    All directory-missing conditions are handled gracefully (return []) and
    logged at WARNING level.  If *warnings_out* is provided, human-readable
    messages are appended to it so the GUI can display them.

    :param shot_list: List of Shot objects to query.
    :param type: Output-type string (must match a key in Constants.DIRECTORY_TYPES).
    :param filter: Case-insensitive substring to filter reviewable names by.
    :param warnings_out: Optional list to collect user-facing warning strings.
    :return: List of Reviewable objects, or None if *shot_list* is empty.
    """
    log.debug(f"Getting reviewables for {shot_list}")
    if not shot_list:
        return None

    if warnings_out is None:
        warnings_out = []

    reviewables: List[reviewable.Reviewable] = []

    # ── Image-based reviewable types ──────────────────────────────────────
    for shot_item in shot_list:
        try:
            if type == 'Comp':
                reviewables += shot_item.get_comps()

            elif type == 'Plate':
                reviewables += shot_item.get_plates()

            elif type == 'Renders':
                render_dir = shot_item.get_render_path()
                reviewables += reviewable.reviewables_from_directory(render_dir)

            elif type == 'Workarea':
                workarea_dir = shot_item.get_workarea_path()
                reviewables += reviewable.reviewables_from_directory(workarea_dir)

            elif type == 'Ref':
                ref_dir = system.Directory(f"{shot_item.get_shot_path()}/ref")
                reviewables += reviewable.reviewables_from_directory(ref_dir)

            elif type == 'Project Files':
                for pf in shot_item.get_project_files():
                    reviewables.append(reviewable.ProjectFileReviewable(pf))

        except Exception as exc:
            msg = f"{type} failed for {shot_item.name}: {exc}"
            log.warning(msg)
            warnings_out.append(msg)

    # ── Database-backed asset reviewables ─────────────────────────────────
    if type == 'Assets':
        try:
            asset_db = data_manager.AssetDataManager()
            asset_reviewables = assetEntry.reviewable_factory(asset_db.get_assets())
            reviewables += asset_reviewables
        except Exception as exc:
            msg = f"Error loading asset reviewables: {exc}"
            log.warning(msg)
            warnings_out.append(msg)

    # ── Filter ────────────────────────────────────────────────────────────
    if filter and filter.strip():
        needle = filter.strip().lower()
        reviewables = [r for r in reviewables if needle in r.asset_name.lower()]
        log.debug(f"Filtered reviewables ({needle}): {reviewables}")

    log.debug(f"Reviewables: {reviewables}")
    return reviewables
