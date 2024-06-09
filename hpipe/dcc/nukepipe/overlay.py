"""
Module for Nuke overlay node. Sets up the callback for knobChanged event for the overlay node.
"""


import nuke
from hpipe.core.hutils import logger

logger = logger.setup_logger()
logger.debug('knobChanged')


def knobChanged():
    if not nuke.thisKnob().node() == nuke.thisNode():
        return

    # DO KNOB CHANGE
    from projectFile import nukeProjectFile
    from importlib import reload
    from utility import path

    node = nuke.thisNode()
    filepath = nuke.root().knob('name').value()

    pf = nukeProjectFile.NukeProjectFile(filepath)

    dirshot = pf.get_shot()
    project = pf.get_project()

    if node.knob('do_override_shot').value() == 1:
        # get project and try override
        if node.knob('do_override_project').value() == 1:
            from db import db
            try:
                project = db.Db().get_project(node.knob('project'))
            except e:
                logger.warning('Invalid override project name')

        # try shot
        try:
            override_shot = node.knob('shot').value()
            dirshot = project.get_shot(override_shot)
        except e:
            logger.warning('Invalid override shot name')
    else:
        logger.debug('no override')
        # do nothing

    node.knob('shot').setValue(dirshot.name)
    node.knob('fend').setValue(str(dirshot.frame_end))
    node.knob('fstart').setValue(str(dirshot.frame_start))
    node.knob('project').setValue(project.name)

def onCreate():
    print('onCreate')