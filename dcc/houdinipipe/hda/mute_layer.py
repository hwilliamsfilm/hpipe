from core.hutils import logger, system
from core import data_manager, constants
import hou
from pxr import Usd, UsdGeom, Sdf

from importlib import reload
reload(logger)
reload(data_manager)
reload(constants)
reload(system)

log = logger.setup_logger()
log.debug("mute_layer.py loaded")


def layer_menu(kwargs) -> list[str]:
    """
    returns the menu for the layer write tool
    """

    shot = hou.getenv("SHOT")
    project = hou.getenv("PROJECT")
    database = data_manager.ProjectDataManager()
    project_instance = database.get_project(project)
    shot_instance = project_instance.get_shot(shot)

    usd_file = shot_instance.get_usd_path()

    stage = Usd.Stage.Open(usd_file.system_path())
    stack = stage.GetLayerStack(includeSessionLayers=False)

    do_core_only = hou.pwd().parm('coreonly').eval()
    core_layers = constants.SHOT_USD_LAYERS

    layer_string_menu = []
    log.debug(f"Stack: {stack}")
    for layer in stack:
        if '/' not in layer.identifier:
            continue
        path = layer.identifier
        filename = path.split('/')[-1]
        name = filename.split('.')[0]
        if do_core_only:
            if name not in core_layers:
                continue
        layer_string_menu.append(path)
        layer_string_menu.append(name)

    return layer_string_menu


def mute_layer() -> bool:
    """
    Mutes the selected layer
    """
    node = hou.pwd()
    stage = node.editableStage()
    layer = node.parent().parm('mutedlayer').eval()
    stage.MuteLayer(layer)
    return True
