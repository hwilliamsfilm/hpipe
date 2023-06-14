
def onCreate():
    import nuke
    node = nuke.thisNode()
    pipe_folder = nuke.Tab_Knob('PIPE')
    node.addKnob(pipe_folder)

def fill_defaults(node):
    from assets import projectFile
    from importlib import reload
    from utility import path
    import nuke
    from utility import logger

    filepath = nuke.root().knob('name').value()
    if not filepath:
        return
    pf = projectFile.ProjectFile(filepath)
    dirshot = pf.get_shot()
    work_area_path = path.fix_path(dirshot.get_workarea_path())

    descriptor = node.knob('descriptor').value()
    version = node.knob('version_1').value()
    format = node.knob('format').value()


    writepath = '{root}/{shotname}_{descriptor}_{version}/{shotname}_{descriptor}_{version}_####.{format}'.format(
        root=work_area_path,
        descriptor=descriptor,
        version=version,
        format=format,
        shotname=dirshot.name
    )

    node.knob('project').setValue(writepath)
    node.knob('file').setValue(writepath)
    node.knob('raw').setValue(1)

    return writepath

def knobChanged():

    # EXIT IF NOT KNOBS
    import nuke
    k = nuke.thisKnob()
    knobs = ['Descriptor', 'Version', 'format', 'Location', 'use_project_version', 'override_shot', 'do_override_shot']
    if k.name() not in knobs:
        return

    # DO KNOB CHANGE
    from assets import projectFile
    from importlib import reload
    from utility import path
    from utility import logger

    node = nuke.thisNode()

    filepath = nuke.root().knob('name').value()

    pf = projectFile.NukeProjectFile(filepath)
    dirshot = pf.get_shot()

    if node.knob('do_override_shot').value() == 1:
        project = pf.get_project()
        try:
            override_shot = node.knob('override_shot').value()
            dirshot = project.get_shot(override_shot)
        except e:
            logger.warning('Invalid override shot name')
    else:
        node.knob('override_shot').setValue(pf.get_shot().name)

    work_area_path = path.fix_path(dirshot.get_workarea_path())
    comp_path = path.fix_path(dirshot.get_comps_path())
    plate_path = path.fix_path(dirshot.get_plate_path())

    descriptor = node.knob('Descriptor').value()
    version = node.knob('Version').value()
    if node.knob('use_project_version').value() == 1:
        version = pf.get_version()
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
            shotname=dirshot.name
        )
    elif 'mov' in f:
        writepath = '{root}/{shotname}_{descriptor}_{version}/{format}/{shotname}_{descriptor}_{version}.{format}'.format(
            root=root,
            descriptor=descriptor,
            version=version,
            format=f,
            shotname=dirshot.name
        )

    node.knob('filepath').setValue(writepath)


def spawnRead():
    return None

def pre_render():
    # DO KNOB CHANGE
    from assets import projectFile
    from importlib import reload
    from utility import path
    from utility import logger

    node = nuke.thisNode()

    filepath = nuke.root().knob('name').value()
    pf = projectFile.ProjectFile(filepath)
    pf.get_version()
    return NotImplementedError

def openDir():
    print('open!')
    import nuke
    import subprocess
    node = nuke.thisNode()
    fullpath = node.knob('filepath').value()
    p = '/'.join(fullpath.split('/')[:-1]) + '/'
    print(p)
    from utility import path
    subprocess.call(["open", p])