"""
This file is run when Houdini starts up. It is used to set up the Houdini session with the necessary environment.
"""

import hou
import sys
import inspect, os

hpipe_base_path = (
    os.path.dirname(
        os.path.dirname(
            os.path.dirname(
                os.path.dirname(
                    os.path.abspath(inspect.getfile(inspect.currentframe()))
                )
            )
        )
    )
)


def install_pypanels() -> bool:
    """
    Installs pypanels into the current Houdini session.
    :return: bool success
    """
    raise NotImplementedError


def extend_scripts() -> bool:
    """
    Adds the scripts directory to the Houdini python path.
    :return: bool success
    """
    sys.path.append(hpipe_base_path)
    sys.path.append(r'/Users/hunterwilliams/PycharmProjects/hloptools')
    return True


def extend_hdas() -> bool:
    """
    Adds the hda directory to the Houdini otl scan path and reloads all otls.
    :return: bool success
    """
    hda_paths = [f"{hpipe_base_path}/hpipe/dcc/houdinipipe/hda/resource"]
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

    shot_loader_type = hou.nodeType(hou.lopNodeTypeCategory(), 'hpipe::shot_loader::1.0')
    shot_loader_type.setDefaultColor(hou.Color(.4, .4, .4))

    mute_layer_type = hou.nodeType(hou.lopNodeTypeCategory(), 'hpipe::mute_layer::1.0')
    mute_layer_type.setDefaultColor(hou.Color(.996, .682, .682))

    write_layer_type = hou.nodeType(hou.lopNodeTypeCategory(), 'hpipe::write_layer::1.0')
    write_layer_type.setDefaultColor(hou.Color(.905, .788, .662))

    configure_shot_layer_type = hou.nodeType(hou.lopNodeTypeCategory(), 'hpipe::configure_shot_layer::1.0')
    configure_shot_layer_type.setDefaultColor(hou.Color(.905, .788, .662))

    return True


# TODO put into try block to avoid preventing Houdini from opening
print('Running houdini startup script...')
extend_scripts()
extend_hdas()
unique_scene_data()
set_node_defaults()
