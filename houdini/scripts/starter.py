"""
123 and 456 scripts for houdini
"""



import hou

import utility.logger


def create123():
    import sys
    import hou

    hda_paths = [
        '$HH/otls/',
        'Y:/_houdini_/hda/',
    ]

    hou.putenv('HOUDINI_OTLSCAN_PATH', ';'.join(hda_paths))
    hou.hda.reloadAllFiles()

    # default scene
    default_scene_path = r'Y:\projects\2023\defaults\shots\default\working_files\houdini\default-set-v001-hunter.hiplc'
    hou.hipFile.merge(default_scene_path, ignore_load_warnings=True)
    utility.logger.log('Loaded default scene: %s' % default_scene_path, 'INFO')

    for node in hou.node('/obj').children():
        if 'scene_data' in node.type().name():
            node.destroy()
            hou.node('/obj').createNode('scene')

    hou.node('/obj').createNode('scene')

    # node defaults
    nulltype = hou.nodeType(hou.sopNodeTypeCategory(), "null")
    nulltype.setDefaultColor(hou.Color(0,0,0))
    nulltype.setDefaultShape('box')

    omergetype = hou.nodeType(hou.sopNodeTypeCategory(), 'object_merge')
    omergetype = omergetype.setDefaultColor(hou.Color(0,0,1))

    farmroptype = hou.nodeType(hou.ropNodeTypeCategory(), 'hunter_farm_rop')
    farmroptype = farmroptype.setDefaultColor(hou.Color(.384,.184,.329))

    filewritetype = hou.nodeType(hou.sopNodeTypeCategory(), 'hunter::main::file_write::1.0')
    filewritetype = filewritetype.setDefaultColor(hou.Color(.384,.184,.329))