"""
Utility functions and classes for managing sequence and shot usd data.
"""

from pxr import Usd, UsdGeom
import system
from core import shot, project


def create_project_usd(usd_path: system.Filepath, project_instance: project.Project) -> system.Filepath:
    """
    Creates a new project usd file at the given path and returns the path to the new file.
    :param usd_path: path to the new usd file
    :param project_instance: project instance to create the usd file for
    :return: path to the new usd file
    """
    raise NotImplementedError


def create_shot_usd(usd_path: system.Filepath, shot_instance: shot.Shot) -> system.Filepath:
    """
    Creates a new shot usd file at the given path and returns the path to the new file.
    :param usd_path: path to the new usd file
    :param shot_instance: shot instance to create the usd file for
    :return: path to the new usd file
    """
    raise NotImplementedError

