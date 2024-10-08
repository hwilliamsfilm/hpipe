from hpipe.core.hutils import logger, system
from hpipe.core import data_manager
from hpipe.core import constants
from pxr import Usd, Sdf
import hou
from pxr import Usd, UsdGeom, Sdf

from importlib import reload
reload(logger)
reload(data_manager)
reload(constants)
reload(system)

log = logger.setup_logger()
log.debug("configure_shot_layer.py loaded")


def major_type_menu(kwargs) -> list[str]:
    """
    returns the menu for the configure layer tool
    """
    import os
    project_name = hou.getenv("PROJECT")
    shot_name = hou.getenv("SHOT")
    database = data_manager.ProjectDataManager()
    project = database.get_project(project_name)
    shot = project.get_shot(shot_name)
    usd_layers = shot.get_major_usd_layers()
    major_type_menu = []
    for layer in usd_layers:
        name = os.path.basename(layer).split(".")[0]
        major_type_menu.append(name)
        major_type_menu.append(layer)
    return major_type_menu


def get_layer_path() -> str:
    """
    gets the layer path given the shot, type, and descriptor
    """
    shot = hou.getenv("SHOT")
    project = hou.getenv("PROJECT")
    database = data_manager.ProjectDataManager()
    project_instance = database.get_project(project)
    shot_instance = project_instance.get_shot(shot)
    major_type = hou.pwd().parm('majortype').eval()
    descriptor = hou.pwd().parm('descriptor').eval()
    layer_path = f"{shot_instance.get_usd_directory().system_path()}/{major_type}/{descriptor}/{descriptor}.usd"
    log.debug(f"Layer path: {layer_path}")
    layer_filepath = system.Filepath(layer_path)
    return layer_filepath.system_path()