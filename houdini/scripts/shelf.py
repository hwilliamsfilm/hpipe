import hou
import os
from utility import logger

# import megascan textures


def megascan_import():
    texture_list = ['Albedo', 'Displacement', 'Roughness', 'AO', 'Normal']

    dir = hou.ui.selectFile(start_directory=hou.getenv('GLOBAL_ASSETS'), file_type=hou.fileType.Directory,
                               image_chooser=True)

    directory_items = os.listdir(dir)
    logger.info(dir)

    root = dir.split('/')[-2].split('_')[-4]
    parent = hou.selectedNodes()[0].parent()
    logger.info(root)

    for item in directory_items:
        for texture in texture_list:
            if texture in item:
                file = '{0}{1}'.format(dir, item)
                image_node = parent.createNode('arnold::image', node_name=item)
                image_node.parm('filename').set(file)
                image_node.moveToGoodPosition()
                logger.info(image_node)

    return


def flipbook():
    import toolutils
    from assets import projectFile
    from utility import logger
    from importlib import reload
    reload(projectFile)

    descriptor = hou.ui.readInput('Description:')[-1]
    s = hou.getenv('SCENE')

    # Frame range logic
    fstart = hou.getenv('FSTART')
    fend = hou.getenv('FEND')
    initial = '{0}-{1}'.format(fstart, fend)
    framerange = hou.ui.readInput('Range(X-X):', initial_contents=initial)[-1].split('-')

    # filepath
    filepath = hou.getenv('HIPFILE')
    projfile = projectFile.HoudiniProjectFile(str(filepath))
    workarea = projfile.get_shot().get_workarea_path()
    flipbookpath = '{workarea}{shot}_{descriptor}/{shot}_{descriptor}_$F4.jpg'.format(workarea=workarea, descriptor=descriptor, shot=s)

    logger.info(flipbookpath)

    #flipbook api
    scene = toolutils.sceneViewer()
    settings = scene.flipbookSettings()
    settings.useResolution(False)

    settings.frameRange((int(framerange[0]),int(framerange[1])))
    settings.output(flipbookpath)

    scene.flipbook(None, settings)

    return True

def megascan_asset_import():
    return