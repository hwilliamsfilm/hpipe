"""
This script is run when a houdini project file is opened. It will check to make sure scene control is up to date.
"""
import hou


def set_houdini_state() -> bool:
    """
    Sets the Houdini state to the default state for the project.
    :return: bool success
    """
    hou.setUpdateMode(hou.updateMode.Manual)
    hou.updateModeSetting()

    return True


def update_scene_control() -> bool:
    """
    Updates the scene control node to the latest version.
    :return: bool success
    """
    for node in hou.node('/obj').children():
        if node.type().name() == 'scene':
            node.destroy()
            hou.node('/obj').createNode('scene')
    hou.node('/obj').createNode('scene')
    return True


set_houdini_state()
update_scene_control()