from hpipe.core.hutils import logger, system
from hpipe.core import data_manager
from hpipe.core import constants
import hou
from pxr import Usd

from importlib import reload
reload(logger)
reload(data_manager)
reload(constants)
reload(system)

log = logger.setup_logger()
log.debug("mute_layer.py loaded")


def _get_usd_shot(filepath) -> str:
    """
    Gets the shot of the current asset.
    """
    log.debug(f"Filepath: {filepath.system_path()}")
    directory_list = filepath.system_path().split('/')
    project_index = directory_list.index('projects')
    shot = directory_list[project_index + 4]
    return shot


def _get_usd_project(filepath) -> str:
    """
    Gets the project of the current asset by looking at the parent directory.
    """
    directory_list = filepath.system_path().split('/')
    project_index = directory_list.index('projects')
    project = directory_list[project_index + 2]
    return project


def layer_menu(kwargs) -> list[str]:
    """
    returns the menu for the layer write tool
    """

    node = hou.pwd()
    try:
        node_input = node.inputs()[0]
    except IndexError:
        log.debug("No input found")
        return []
    stage = node_input.stage()
    stack = stage.GetLayerStack(includeSessionLayers=False)
    print(stack)
    do_core_only = node.parm('coreonly').eval()

    core_layers = constants.SHOT_USD_LAYERS

    layer_string_menu = ['', 'None']
    for layer in stack:
        if '/' not in layer.identifier:
            continue

        path = layer.identifier
        filename = path.split('/')[-1]
        name = filename.split('.')[0]

        # get shot name
        path_corrected = path.replace(r"y:/", r"Y:/") # IDK why but usd really likes to lowercase the drive letter

        # find string after /shots/ in path
        shot_name = path_corrected.split('/shots/')[1].split('/')[0]

        if do_core_only:
            if name not in core_layers:
                continue

        layer_string_menu.append(path)
        layer_string_menu.append(f"{shot_name}: {filename}") #label

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
