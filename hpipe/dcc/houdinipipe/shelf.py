"""
Houdini module for shelf scripts.

PROJECT FILE -> ../../../shot_task_desc_version.hiplc
"""
import hou
from hpipe.assets import projectFile
from hpipe.core.hutils import logger, system
from hpipe.dcc.houdinipipe import session
from hpipe.core import data_manager

from typing import *

log = logger.setup_logger()
log.debug("shelf.py loaded")


def save_new_version() -> bool:
    """
    Saves a new version of the current project file.
    :returns: True if the save was successful, False otherwise.
    """
    sesh = session.HoudiniSession()
    if sesh.version:
        sesh.version = (sesh.version[0], sesh.version[1] + 1)
    else:
        sesh.version = ('A', 1)
    new_filepath = sesh.get_filepath()
    if not new_filepath:
        return False
    hou.hipFile.save(new_filepath.system_path())
    return True

