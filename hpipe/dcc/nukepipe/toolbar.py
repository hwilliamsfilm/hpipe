"""
General pipe toolbar for Nuke
"""

from hpipe.core import data_manager
from hpipe.assets import projectFile
from hpipe.core.hutils import logger, system

log = logger.setup_logger()
log.debug("Loaded hpipe.dcc.nukepipe.toolbar")


def version_up():
    """
    Version up the current script
    """
    import nuke
    import os
    import re

    # project_database = data_manager.ProjectDataManager()
    filepath = nuke.root().knob('name').value()
    log.debug(f"Filepath: {filepath}")

    nuke_projectFile = projectFile.NukeProjectFile(system.Filepath(filepath))
    shot = nuke_projectFile.get_asset_shot()
    project = nuke_projectFile.get_asset_project()

    if not shot or not project:
        log.error("Could not find shot or project")

    print("Versioning up")
