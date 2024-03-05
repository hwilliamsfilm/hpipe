"""
Utility functions for the manager class and other classes that use the manager class.
"""

from typing import *

from hpipe.core import shot
from hpipe.core.hutils import logger

if TYPE_CHECKING:
    from hpipe.core import project

log = logger.setup_logger()
log.debug("pipeConfig_utils.py loaded")


def shots_from_dict(shot_dictionary: dict, parent_project: 'project.Project') -> List['shot.Shot']:
    """
    Creates a list of shot objects from a dictionary. Extracting this from the project class to
    create shot objects with references to the project class.
    :param shot_dictionary: dict of shots
    :param parent_project: parent project instance
    :return: list of shot objects
    """

    shots = []

    if shot_dictionary:
        for shot_name, shot_dict in shot_dictionary.items():
            shot_object = shot.Shot.from_dict(shot_dict, parent_project)
            shots.append(shot_object)

    return shots
