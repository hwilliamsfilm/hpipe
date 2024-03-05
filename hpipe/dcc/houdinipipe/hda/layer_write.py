from hpipe.core.hutils import logger, system
from hpipe.core import data_manager
from hpipe.core import constants
import hou

from importlib import reload
reload(logger)
reload(data_manager)
reload(constants)
reload(system)

log = logger.setup_logger()
log.debug("layer_write.py loaded")


def layer_menu(kwargs) -> list[str]:
    """
    returns the menu for the layer write tool
    """
    shot = hou.getenv("SHOT")
    project = hou.getenv("PROJECT")
    database = data_manager.ProjectDataManager()
    project_instance = database.get_project(project)
    shot_instance = project_instance.get_shot(shot)

    layers = constants.SHOT_USD_LAYERS

    layer_string_menu = []

    for layer in layers:
        layer_path = f"{shot_instance.get_usd_directory().system_path()}/{layer}/{layer}.usda"
        log.debug(f"Layer path: {layer_path}")
        layer_filepath = system.Filepath(layer_path)
        layer_string_menu.append(layer_filepath.system_path())
        layer_string_menu.append(layer)

    return layer_string_menu
