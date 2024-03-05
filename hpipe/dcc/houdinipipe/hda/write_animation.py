from hpipe.core.hutils import logger, system
from hpipe.core import data_manager
from hpipe.core import constants
import hou

log = logger.setup_logger()
log.debug("write_animation.py loaded")


def get_root_path() -> str:
    """
    gets the layer path given the shot, type, and descriptor
    """
    shot = hou.getenv("SHOT")
    project = hou.getenv("PROJECT")
    node = hou.pwd()
    asset = node.parm('assetanimation').eval()

    if asset == 1:
        config_manager = data_manager.ConfigDataManager()
        asset_root = config_manager.get_config("ASSETS_ROOT")
        asset_name = node.parm('assetname').eval()
        descriptor = hou.pwd().parm('descriptor').eval()
        root_path = f"{asset_root}/{asset_name}/{descriptor}"
        log.debug(f"Root path: {root_path}")

    else:
        log.warning('LOADING DATABASE')
        database = data_manager.ProjectDataManager()
        project_instance = database.get_project(project)
        shot_instance = project_instance.get_shot(shot)
        descriptor = hou.pwd().parm('descriptor').eval()
        root_path = f"{shot_instance.get_usd_directory().system_path()}/geometry/{descriptor}"


    log.debug(f"Root path: {root_path}")
    root_filepath = system.Filepath(root_path)
    node.parm('rootpathcook').set(root_filepath.system_path())
    return root_filepath.system_path()

def get_root_path_parm() -> str:
    """
    gets the layer path given the shot, type, and descriptor
    """
    root_path = hou.pwd().parm('rootpathcook').eval()
    log.debug(f"Root path: {root_path}")
    return root_path


def get_topology_path() -> str:
    """
    gets the layer path given the shot, type, and descriptor
    """
    root_path = hou.pwd().parm('rootpathcook').eval()
    topology_path = f"{root_path}/topology.usda"
    log.debug(f"Topology path: {topology_path}")
    topology_filepath = system.Filepath(topology_path)
    return topology_filepath.system_path()


def get_manifest_path() -> str:
    """
    gets the layer path given the shot, type, and descriptor
    """
    root_path = hou.pwd().parm('rootpathcook').eval()
    manifest_path = f"{root_path}/manifest.usda"
    log.debug(f"Manifest path: {manifest_path}")
    manifest_filepath = system.Filepath(manifest_path)
    return manifest_filepath.system_path()


def get_geometry_path() -> str:
    """
    gets the layer path given the shot, type, and descriptor
    """
    root_path = hou.pwd().parm('rootpathcook').eval()
    descriptor = hou.pwd().parm('descriptor').eval()
    frame: float = hou.frame()
    padzero_frame = int(str(int(frame)).zfill(4))
    geometry_path = f"{root_path}/geometry/{descriptor}_{padzero_frame}.usd"
    log.debug(f"Geometry path: {geometry_path}")
    geometry_filepath = system.Filepath(geometry_path)
    return geometry_filepath.system_path()


def get_layer_path() -> str:
    """
    gets the layer path given the shot, type, and descriptor
    """
    root_path = hou.pwd().parm('rootpathcook').eval()
    descriptor = hou.pwd().parm('descriptor').eval()
    layer_path = f"{root_path}/{descriptor}.usda"
    log.debug(f"Layer path: {layer_path}")
    layer_filepath = system.Filepath(layer_path)
    return layer_filepath.system_path()


def update_root_parm() -> None:
    """
    updates the root path parm
    """
    root_path = get_root_path()
    hou.pwd().parm('rootpathcook').set(root_path)
