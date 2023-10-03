"""
Python module for the scene control pipe node.
"""
from typing import *
import hou
from core import data_manager
from assets import projectFile
from enum import Enum
from core.hutils import logger

# from importlib import reload

log = logger.setup_logger()
log.debug("scene_control.py loaded")


class SceneControlConstants(Enum):
    """
    Enum for the scene control constants.
    """
    shot_global_vars: List[str] = [
        'SHOT',
        'SHOT_PATH',
        'SAVE_PATH',
        'OUTPUT_PATH',
        'CACHE_PATH',
        'RENDER_PATH'
    ]

    project_global_vars: List[str] = [
        'PROJECT',
        'PROJ_FPS',
        'PROJECT_PATH',
        'SHOTS_PATH',
        'ASSETS_PATH'
    ]


def unset_globals(scope: str = 'project') -> bool:
    """
    Set the global variables for the scene control node.
    :param scope: The scope of the global variables to set. Can either be 'shot' or 'project'.
    :return: True if successful
    """
    environment_variables = None
    if scope == 'project':
        environment_variables = SceneControlConstants.project_global_vars.value
    if scope == 'shot':
        environment_variables = SceneControlConstants.shot_global_vars.value
    if not environment_variables:
        return False
    for env_var in environment_variables:
        hou.unsetenv(env_var)
        log.debug(env_var)

    return True


def set_global(global_name: str, global_value: str) -> bool:
    """
    Set an environment variable in houdini.
    :param global_name: Name of the global to be set.
    :param global_value: Value of the global to be set.
    :returns: True if successful.
    """
    # Need to set in the hou.putenv (true environment variable) and the variables and aliases which
    # is the hscript version

    log.debug(f'Set {global_name} to {global_value}')
    hou.putenv(global_name, global_value)
    hou.hscript("setenv {0} = {1}".format(global_name, global_value))
    return True


def on_loaded() -> bool:
    """
    Run on loaded script for the scene control node.
    """
    raise NotImplementedError


def on_created() -> bool:
    """
    Run on created script for the scene control node.
    """
    raise NotImplementedError


def project_menu() -> List[str]:
    """
    Get a list of the projects and return it as a formatted houdini list.
    """
    project_list = data_manager.ProjectDataManager().get_projects()
    menu = []
    for project in project_list:
        menu.append(project.name)
        menu.append(project.name)
    return menu


def shot_menu() -> List[str]:
    """
    Get a list of the shots and return it as a formatted houdini list.
    """
    menu = []
    name = hou.getenv('PROJECT')
    project = data_manager.ProjectDataManager().get_project(name)
    for shot in project.get_shots():
        menu.append(shot.name)
        menu.append(shot.name)
    return menu


def hip_menu() -> List[str]:
    """
    Get a list of the available hip files and return it as a formatted houdini list.
    :return: A list of the available hip files.
    """
    database = data_manager.ProjectDataManager()
    project_name = hou.getenv('PROJECT')
    shot_name = hou.getenv('SHOT')
    if not shot_name or not project_name:
        return []
    if shot_name == '-' or project_name == '-':
        return []
    if shot_name == '' or project_name == '':
        return []

    project = database.get_project(project_name)
    shot = project.get_shot(shot_name)
    hip_file_path = shot.get_houdini_path()
    hip_files = projectFile.project_files_from_directory(hip_file_path)
    menu = []
    for hip_file in hip_files:
        menu.append(hip_file.filepath.system_path())
        menu.append(hip_file.filepath.system_path())
    return menu


def set_project(kwargs: Dict[Any, Any]) -> bool:
    """
    Set the project based on the selected project in the scene control node.
    :param kwargs: The kwargs from the houdini event handler.
    :return: True if successful.
    """
    node = kwargs['node']
    project_name = kwargs['script_value']

    node.parm('shot').set('')

    unset_globals('project')
    unset_globals('shot')

    no_project = project_name == '-' or project_name == ''
    if no_project:
        unset_globals('project')
        node.cook(True)
        return False

    database = data_manager.ProjectDataManager()
    project = database.get_project(project_name)

    # TODO: potentially this should be a for loop over the shot global vars enum
    set_global('PROJECT', project.name)
    set_global('PROJECT_PATH', project.get_project_path())
    set_global('SHOTS_PATH', project.get_shot_path())
    set_global('PROJECT_ASSETS_PATH', project.get_assets_path())
    set_global('PROJ_FPS', str(24))

    node.cook(True)
    return True


def set_shot(kwargs) -> bool:
    """
    Set the shot based on the selected shot in the scene control node. If no shot is selected, unset all shot
    variables.
    :param kwargs: The kwargs from the houdini event handler.
    :return: True if successful.
    """
    node = kwargs['node']
    shot_name = node.evalParm('shot')

    no_shot = shot_name == '-' or shot_name == ''
    if no_shot:
        unset_globals('shot')
        node.cook(True)
        return False

    database = data_manager.ProjectDataManager()

    project_name = hou.getenv('PROJECT')
    project = database.get_project(project_name)

    shot = project.get_shot(shot_name)

    # TODO: potentially this should be a for loop over the shot global vars enum
    set_global('SHOT', shot.name)
    set_global('SHOT_PATH', shot.get_shot_path())
    set_global('SAVE_PATH', shot.get_houdini_path().system_path())
    set_global('OUTPUT_PATH', shot.get_render_path().system_path())
    set_global('CACHE_PATH', shot.get_cache_path())
    set_global('RENDER_PATH', shot.get_render_path().system_path())
    set_global('FSTART', str(shot.frame_start))
    set_global('FEND', str(shot.frame_end))

    hou.playbar.setFrameRange(float(shot.frame_start), float(shot.frame_end))
    hou.playbar.setPlaybackRange(float(shot.frame_start), float(shot.frame_end))

    node.cook(True)
    return True


def load_hip_file() -> bool:
    """
    Load the selected hip file.
    """
    raise NotImplementedError
