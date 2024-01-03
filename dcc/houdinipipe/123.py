"""
This file is run when Houdini starts up. It is used to set up the Houdini session with the necessary environment.
"""

import hou
import sys
# from enum import Enum
# from core.hutils import system


# TODO: make these paths relative or move them to the config file
class HoudiniPipe:
    """
    Enum for the houdini pipe.
    """
    stable_pipe = [
        r"/Users/hunterwilliams/PycharmProjects/hpipe",
    ]
    stable_hda = [
        r'$HH/otls/',
        r'/Users/hunterwilliams/PycharmProjects/hpipe/dcc/houdinipipe/hda/resource',
    ]

    dev_pypanels = [r'/Volumes/hlw01/hpipe/hpipe/dcc/houdinipipe/hda/resource/pipeManager.pypanel']


def install_pypanels() -> bool:
    """
    Installs pypanels into the current Houdini session.
    :return: bool success
    """
    pypanels = HoudiniPipe.dev_pypanels
    for panel in pypanels:
        hou.pypanel.installFile(panel)
    return True


def extend_scripts() -> bool:
    """
    Adds the scripts directory to the Houdini python path.
    :return: bool success
    """
    import_list = HoudiniPipe.stable_pipe
    print('import_list')

    for scripts_path in import_list:
        # scripts_path = system.Filepath(scripts_path).system_path()
        sys.path.append(scripts_path)

    return True


def extend_hdas() -> bool:
    """
    Adds the hda directory to the Houdini otl scan path and reloads all otls.
    :return: bool success
    """
    hda_paths = (HoudiniPipe.stable_hda)
    hou.putenv('HOUDINI_OTLSCAN_PATH', ';'.join(hda_paths))
    hou.hda.reloadAllFiles()

    return True


def add_default_scene() -> bool:
    """
    Adds the default scene to the current Houdini session.
    :return: bool success
    """
    default_scene_path = r'Y:\projects\2023\defaults\shots\default\working_files\houdini\default-set-v001-hunter.hiplc'
    # TODO: default scene should be included in the houdinipipe package and referenced from there
    hou.hipFile.merge(default_scene_path, ignore_load_warnings=True)
    return True


def unique_scene_data() -> bool:
    """
    Removes any existing scene_data nodes and creates a new one. We don't need to worry about persisting parameters
    since all of the data is stored in the project's globals.
    :return: bool success
    """
    for node in hou.node('/obj').children():
        if node.type().name() == 'scene':
            node.destroy()
            hou.node('/obj').createNode('scene')
    hou.node('/obj').createNode('scene')
    return True


def set_node_defaults() -> bool:
    """
    Sets default colors and shapes for nodes.
    :return: bool success
    """

    null_node_type = hou.nodeType(hou.sopNodeTypeCategory(), "null")
    null_node_type.setDefaultColor(hou.Color(0, 0, 0))
    null_node_type.setDefaultShape('box')

    object_merge_type = hou.nodeType(hou.sopNodeTypeCategory(), 'object_merge')
    object_merge_type.setDefaultColor(hou.Color(0, 0, 1))

    shot_loader_type = hou.nodeType(hou.lopNodeTypeCategory(), 'hunterwilliams::shot_loader::1.0')
    shot_loader_type.setDefaultColor(hou.Color(.4, .4, .4))

    mute_layer_type = hou.nodeType(hou.lopNodeTypeCategory(), 'hunterwilliams::mute_layer::1.0')
    mute_layer_type.setDefaultColor(hou.Color(.996, .682, .682))

    write_layer_type = hou.nodeType(hou.lopNodeTypeCategory(), 'hunterwilliams::write_layer::1.0')
    write_layer_type.setDefaultColor(hou.Color(.905, .788, .662))

    configure_shot_layer_type = hou.nodeType(hou.lopNodeTypeCategory(), 'hunterwilliams::configure_shot_layer::1.0')
    configure_shot_layer_type.setDefaultColor(hou.Color(.905, .788, .662))

    return True


# TODO put into try block to avoid preventing Houdini from opening
print('Running houdini startup script...')
extend_scripts()
extend_hdas()
# add_default_scene()
unique_scene_data()
set_node_defaults()
# install_pypanels() # TODO add pypanels to be installed



"""
#
# Houdini Environment Settings
#
# The contents of this file are read into the environment
# at startup.  They will override any existing entries in
# the environment.
#
# The syntax is one entry per line as follows:
#    VAR = VALUE
#
# Values may be quoted
#    VAR = "VALUE"
#
# Values may be empty
#    VAR =
#

# Example:
#
# HOUDINI_NO_SPLASH = 1


# DEFAULTS


HOUDINI_SPLASH_FILE = "/Volumes/hlw01/_houdini_\config\splash\splash_04.jpg"
# OCIO = "/Volumes/hlw01/_global_assets\aces\OpenColorIO-Configs-master\aces_1.0.3\config.ocio"

# "Y:\hpipe\dcc\houdinipipe;&;"

# HOUDINI_SCRIPT_PATH = "/Volumes/hlw01/hpipe/dcc/houdinipipe;&;"


# Project Tools

# PROJ_CONFIG = "/Volumes/hlw01/_houdini_/config/proj_list.json"
# PROJ_ROOT = "/Volumes/hlw01/projects/"

# ICON = "/Volumes/hlw01/_houdini_/icons"


# HOUDINI_DSO_ERROR = 2
# PATH = "C:/ProgramData/Redshift/bin;$PATH"
# HOUDINI_PATH = "C:/ProgramData/Redshift/Plugins/Houdini/${HOUDINI_VERSION};&"

"""

