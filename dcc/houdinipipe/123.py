"""
This file is run when Houdini starts up. It is used to set up the Houdini session with the necessary environment.
"""

import hou
# from core.hutils import system
import sys
from enum import Enum


# TODO: make these paths relative or move them to the config file
class HoudiniPipe(Enum):
    """
    Enum for the houdini pipe.
    """
    stable_pipe = [
        'Y:/_houdini_/scripts/',
        'Y:/_dev/',
        'Y:/_pipe/'
    ]
    dev_pipe = ['Y:/hpipe']
    stable_hda = [
        '$HH/otls/',
        'Y:/_houdini_/hda/',
    ]
    dev_hda = ['Y:/hpipe/dcc/houdinipipe/hda/resource']

    dev_pypanels = ['Y:/hpipe/dcc/houdinipipe/hda/resource/pipeManager.pypanel']


def install_pypanels() -> bool:
    """
    Installs pypanels into the current Houdini session.
    :return: bool success
    """
    pypanels = HoudiniPipe.dev_pypanels.value
    for panel in pypanels:
        hou.pypanel.installFile(panel)
    return True


def extend_scripts() -> bool:
    """
    Adds the scripts directory to the Houdini python path.
    :return: bool success
    """
    import_list = HoudiniPipe.dev_pipe.value

    for scripts_path in import_list:
        sys.path.append(scripts_path)

    return True


def extend_hdas() -> bool:
    """
    Adds the hda directory to the Houdini otl scan path and reloads all otls.
    :return: bool success
    """
    hda_paths = HoudiniPipe.dev_hda.value
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

    # farm_rop_type = hou.nodeType(hou.ropNodeTypeCategory(), 'hunter_farm_rop')
    # farm_rop_type.setDefaultColor(hou.Color(.384, .184, .329))

    # file_write_type = hou.nodeType(hou.sopNodeTypeCategory(), 'hunter::main::file_write::1.0')
    # file_write_type.setDefaultColor(hou.Color(.384, .184, .329))

    return True


# TODO put into try block to avoid preventing Houdini from opening
extend_scripts()
extend_hdas()
add_default_scene()
unique_scene_data()
set_node_defaults()
install_pypanels() # TODO add pypanels to be installed

