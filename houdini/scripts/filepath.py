import hou
from utility import logger
from utility import constants

def get_render_path(deep=False):
    from core import db
    from assets import projectFile
    from pprint import pprint

    # get globals from hipfile
    project_name = hou.getenv('PROJECT')
    shot_name = hou.getenv('SCENE')

    # get shot object
    render_path = hou.getenv('RENDER_PATH')

    # get filepath info
    projectfile = projectFile.HoudiniProjectFile(hou.getenv('HIPFILE'))
    file_info = projectfile.get_hip_info()
    task = file_info['task']
    version = file_info['ver']
    logger.info(projectfile)

    # get node info
    node_name = hou.pwd().name()

    path = '{render_path}/{task}-{node_name}-v{version}/{task}-{node_name}-v{version}_{frame}.exr'.format(
        render_path=render_path,
        task=task, node_name=node_name, version=version, frame=int(hou.frame()))

    if deep:
        path = '{render_path}/{task}-{node_name}-v{version}/{task}-{node_name}-v{version}_deep_{frame}.exr'.format(
            render_path=render_path,
            task=task, node_name=node_name, version=version, frame=int(hou.frame()))

    logger.info(path)
    return str(path)

def get_usd_path(megascan=True):
    if megascan:
        return '{0}/megascan_library/'.format(constants.USD_LIB)
    return constants.USD_LIB

def spawn_usd_material(kwargs):
    print(kwargs)
    return

