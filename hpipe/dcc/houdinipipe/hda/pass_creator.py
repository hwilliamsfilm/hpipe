"""
This script creates a new pass in the render product node and sets the file name attribute for the beauty and deep passes.
"""


def get_pass_path(node: 'hou.Node') -> str:
    """
    Get the file name attribute for the beauty and deep passes in the render product node.
    """
    from hpipe.core import data_manager
    import hou

    parent = node.parent()

    project_name = parent.parm('passproject').eval()
    shot_name = parent.parm('passshot').eval()
    pass_name = parent.parm('passname').eval()
    pass_version_major = parent.parm('passversionmajor').eval()
    pass_version_minor = parent.parm('passversionminor').eval()
    pass_version_minor = str(pass_version_minor).zfill(3)
    hip_file = hou.hipFile.name().split('/')[-1].split('.')[0].split('-')[:-1]
    hip_file = '-'.join(hip_file)
    project = data_manager.ProjectDataManager().get_project(project_name)
    shot = project.get_shot(shot_name)
    render_path = shot.get_render_path()

    pass_path = (f'{render_path.system_path()}/{hip_file}/'
                 f'{pass_name}_{pass_version_major}{pass_version_minor}/'
                 f'{pass_name}_{pass_version_major}{pass_version_minor}')
    return pass_path


def set_pass_path(node: 'hou.Node'):
    """
    Set the file name attribute for the beauty and deep passes in the render product node.
    """
    from pxr import Usd
    import hou

    node = hou.pwd()

    base_pass_path = get_pass_path(node)
    stage = node.editableStage()
    render_products = [x for x in stage.Traverse() if x.GetTypeName() == 'RenderProduct']

    frame_start = int(hou.playbar.frameRange()[0])
    frame_end = int(hou.playbar.frameRange()[1]) + 1

    for prod in render_products:
        file_attr = prod.GetAttribute('productName')

        if prod.GetName() == 'renderproduct':  # set beauty pass
            for frame in range(frame_start, frame_end):
                timesample = Usd.TimeCode(float(frame))
                file_attr.Set(f'{base_pass_path}_{str(frame)}.exr', timesample)

        if prod.GetName() == 'dcm':  # set deep pass
            for frame in range(frame_start, frame_end):
                timesample = Usd.TimeCode(float(frame))
                file_attr.Set(f'{base_pass_path}_deep_{str(frame)}.exr', timesample)

