
from hpipe.core.hutils import logger
log = logger.setup_logger()
log.debug("filewrite.py loaded")

def onCreate():
    import nuke
    node = nuke.thisNode()
    pipe_folder = nuke.Tab_Knob('PIPE')
    node.addKnob(pipe_folder)


def fill_defaults(node):
    """
    Fills the defaults for the filewrite node when the knob is changed.
    """
    import nuke
    from hpipe.assets import projectFile
    from hpipe.core.hutils import system
    from hpipe.core import data_manager

    project_database = data_manager.ProjectDataManager()
    filepath = nuke.root().knob('name').value()
    if not filepath:
        return

    nuke_projectFile = projectFile.NukeProjectFile(system.Filepath(filepath))
    shot = nuke_projectFile.get_asset_shot()
    project = nuke_projectFile.get_asset_project()
    pipe_shot = project_database.get_project(project).get_shot(shot)
    work_area_path = pipe_shot.get_workarea_path().system_path()

    descriptor = node.knob('descriptor').value()
    version = node.knob('version_1').value()
    format = node.knob('format').value()

    writepath = '{root}/{shotname}_{descriptor}_{version}/{shotname}_{descriptor}_{version}_####.{format}'.format(
        root=work_area_path,
        descriptor=descriptor,
        version=version,
        format=format,
        shotname=pipe_shot.name
    )

    node.knob('project').setValue(writepath)
    node.knob('file').setValue(writepath)
    node.knob('raw').setValue(1)

    return writepath


def knobChanged():
    """
    Currently, this function will execute whenever a knob is changed in the entire nuke session.
    # TODO is this the best way to do this? Is there a smaller scope?
    """

    import nuke
    # EXIT IF NOT KNOBS

    k = nuke.thisKnob()
    knobs = ['Descriptor', 'Version', 'format', 'Location', 'use_project_version', 'override_shot', 'do_override_shot']
    if k.name() not in knobs:
        return

    # DO KNOB CHANGE
    import nuke
    from hpipe.assets import projectFile
    from hpipe.core.hutils import system
    from hpipe.core import data_manager

    node = nuke.thisNode()

    project_database = data_manager.ProjectDataManager()
    filepath = nuke.root().knob('name').value()
    log.debug(f"Filepath: {filepath}")

    nuke_projectFile = projectFile.NukeProjectFile(system.Filepath(filepath))
    shot = nuke_projectFile.get_asset_shot()
    project = nuke_projectFile.get_asset_project()

    log.debug(f"Shot: {shot}")
    log.debug(f"Project: {project}")

    pipe_shot = project_database.get_project(project).get_shot(shot)
    pipe_project = project_database.get_project(project)

    if node.knob('do_override_shot').value() == 1:
        try:
            override_shot = node.knob('override_shot').value()
            pipe_shot = pipe_project.get_shot(override_shot)
        except Exception as e:
            print(e)
    else:
        node.knob('override_shot').setValue(pipe_shot.name)

    log.debug(f"Shot: {pipe_shot}")
    log.debug(f"workarea: {pipe_shot.get_workarea_path()}")
    work_area_path = pipe_shot.get_workarea_path().system_path()
    comp_path = pipe_shot.get_comps_path().system_path()
    plate_path = pipe_shot.get_plate_path().system_path()

    descriptor = node.knob('Descriptor').value()
    version = node.knob('Version').value()

    if node.knob('use_project_version').value() == 1:
        version_tuple = nuke_projectFile.get_version()
        version = f"{version_tuple[0]}{version_tuple[1]:02d}"
        node.knob('Version').setValue(version)

    f = node.knob('format').value()
    location = node.knob('Location').value()

    asset_name = nuke_projectFile.get_asset_name()

    root = ''
    writepath = ''

    if location == 'workarea':
        root = work_area_path
    elif location == 'comp':
        root = comp_path
    elif location == 'plate':
        root = plate_path

    if 'mov' not in f:
        writepath = '{root}/{shotname}_{descriptor}_{version}/{format}/{shotname}-{task}-{descriptor}-{version}_####.{format}'.format(
            root=root,
            descriptor=descriptor,
            version=version,
            format=f,
            shotname=pipe_shot.name,
            task=asset_name
        )
    elif 'mov' in f:
        writepath = '{root}/{shotname}_{descriptor}_{version}/{format}/{shotname}-{task}-{descriptor}-{version}.{format}'.format(
            root=root,
            descriptor=descriptor,
            version=version,
            format=f,
            shotname=pipe_shot.name,
            task=asset_name
        )

    node.knob('filepath').setValue(writepath)
