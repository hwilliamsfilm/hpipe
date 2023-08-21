import hou
from core.hutils import system


def install_pypanels() -> bool:
    """
    Installs pypanels into the current Houdini session.
    :return: bool success
    """
    pypanels: list[system.Filepath] = []
    for panel in pypanels:
        hou.pypanel.installFile(panel)
    return True

install_pypanels()