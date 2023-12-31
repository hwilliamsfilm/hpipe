# """
# This script is run when a houdini project file is opened. It will check to make sure scene control is up to date.
# """
# import hou
#
#
# def set_houdini_state() -> bool:
#     """
#     Sets the Houdini state to the default state for the project.
#     :return: bool success
#     """
#     hou.setUpdateMode(hou.updateMode.Manual)
#     hou.updateModeSetting()
#
#     return True
#
#
# def update_scene_control() -> bool:
#     """
#     Updates the scene control node to the latest version.
#     :return: bool success
#     """
#
#     scene_control_nodes = hou.objNodeTypeCategory().nodeType('hlw::scene::3.0')
#
#     for node in scene_control_nodes.instances():
#         node.destroy()
#
#     hou.node('/obj').createNode('hlw::scene::3.0')
#     return True
#
#
# set_houdini_state()
# update_scene_control()
#
