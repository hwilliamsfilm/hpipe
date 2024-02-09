
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
    from assets import projectFile
    from core.hutils import system
    from core import data_manager

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

    import nuke
    # EXIT IF NOT KNOBS

    k = nuke.thisKnob()
    knobs = ['Descriptor', 'Version', 'format', 'Location', 'use_project_version', 'override_shot', 'do_override_shot']
    if k.name() not in knobs:
        return

    # DO KNOB CHANGE
    import nuke
    from assets import projectFile
    from core.hutils import system
    from core import data_manager

    node = nuke.thisNode()

    project_database = data_manager.ProjectDataManager()
    filepath = nuke.root().knob('name').value()

    nuke_projectFile = projectFile.NukeProjectFile(system.Filepath(filepath))
    shot = nuke_projectFile.get_asset_shot()
    project = nuke_projectFile.get_asset_project()
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

    work_area_path = pipe_shot.get_workarea_path().system_path()
    comp_path = pipe_shot.get_comps_path().system_path()
    plate_path = pipe_shot.get_plate_path().system_path()

    descriptor = node.knob('Descriptor').value()
    version = node.knob('Version').value()

    if node.knob('use_project_version').value() == 1:
        version = nuke_projectFile.get_version()
        node.knob('Version').setValue(version)

    f = node.knob('format').value()
    location = node.knob('Location').value()

    root = ''
    writepath = ''

    if location == 'workarea':
        root = work_area_path
    elif location == 'comp':
        root = comp_path
    elif location == 'plate':
        root = plate_path

    if 'mov' not in f:
        writepath = '{root}/{shotname}_{descriptor}_{version}/{format}/{shotname}_{descriptor}_{version}_####.{format}'.format(
            root=root,
            descriptor=descriptor,
            version=version,
            format=f,
            shotname=pipe_shot.name
        )
    elif 'mov' in f:
        writepath = '{root}/{shotname}_{descriptor}_{version}/{format}/{shotname}_{descriptor}_{version}.{format}'.format(
            root=root,
            descriptor=descriptor,
            version=version,
            format=f,
            shotname=pipe_shot.name
        )

    node.knob('filepath').setValue(writepath)


# def spawnRead():
#     return None
#
# def pre_render():
#     return NotImplementedError
#
# def openDir():
#     print('open!')
#     import nuke
#     import subprocess
#     node = nuke.thisNode()
#     fullpath = node.knob('filepath').value()
#     p = '/'.join(fullpath.split('/')[:-1]) + '/'
#     print(p)
#     from utility import path
#     subprocess.call(["open", p])