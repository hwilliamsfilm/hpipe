"""
This module contains functions for dealing with file paths.
"""
import os
import platform
from enum import Enum
from assets import asset
from core.hutils import path

LINUX_ROOT = r'/mnt/share/hlw01/'
WINDOWS_ROOT = r'Y:/'
OSX_ROOT = r'/Volumes/hlw01/'


class System(Enum):
    OSX = 'osx'
    WINDOWS = 'windows'
    LINUX = 'linux'


class Directory:
    """
    Base class for a directory on disk. This class is meant to be very generic and only describe the most basic
    properties of a directory. It is meant to be subclassed to create more specific directory types.
    """
    def __init__(self, directory_path: str, directory_name: str = ''):
        self.directory_path = path.fix_path(directory_path)
        if directory_name == '':
            directory_name = os.path.basename(directory_path)
        self.directory_name = directory_name

    def get_files(self) -> list['Filepath']:
        """
        Returns a list of all files in the directory.
        """
        directory_files: list[Filepath] = []
        for root, dirs, files in os.walk(self.directory_path):
            for file in files:
                directory_files.append(Filepath(os.path.join(root, file)))

        return directory_files


class Filepath:
    """
    Base class for a filepath. This class is meant to be very generic and only describe the most basic
    properties of a filepath. It is meant to be subclassed to create more specific filepath types, like images,
    project files, etc.
    """

    def __init__(self, filepath_path: str, filepath_name: str = ''):
        self.filepath_path = path.fix_path(filepath_path)
        if filepath_name == '':
            filepath_name = os.path.basename(filepath_path)
        self.filepath_name = filepath_name
        self.basename = os.path.basename(filepath_path)
        self.extension = os.path.splitext(filepath_path)[1]
        self.system = self.get_path_system()
        self.system_root = self.get_root()

    def __repr__(self):
        return f'Filepath({self.filepath_path})'

    def has_frame_number(self) -> bool:
        """
        Checks if the filepath has a frame number.
        :return: True if the filepath has a frame number, False if not
        """
        has_number_in_name = any(char.isdigit() for char in self.basename)

        if not has_number_in_name:
            return False

        if '_' not in self.basename:
            return False

        return True

    def get_frame_number(self) -> int:
        """
        Gets the frame number from the filepath. The format is assumed to be: name_####.ext
        :return: frame number
        """
        if not self.has_frame_number():
            return -1
        frame_number: int = int(self.basename.split('_')[-1].split('.')[0])
        return frame_number

    def get_path_system(self) -> System:
        """
        Returns the current system
        """
        if LINUX_ROOT in self.filepath_path:
            return System.LINUX
        if WINDOWS_ROOT in self.filepath_path:
            return System.WINDOWS
        if OSX_ROOT in self.filepath_path:
            return System.OSX
        raise ValueError('Filepath does not contain a valid system root.')

    def get_root(self) -> str:
        """
        Returns the root path for the current system
        """
        if self.system == System.LINUX:
            return LINUX_ROOT
        if self.system == System.WINDOWS:
            return WINDOWS_ROOT
        if self.system == System.OSX:
            return OSX_ROOT
        raise ValueError('Filepath does not contain a valid system root.')

    def system_path(self) -> str:
        """
        Returns the path for the current system
        """
        # remove the system root from the path
        sys_config = SystemConfig()
        environment = sys_config.system
        if environment != self.system:
            return self.filepath_path.replace(self.system_root, sys_config.system_root)
        else:
            return self.filepath_path

    def get_extension(self) -> str:
        """
        Returns the extension of a file path
        """
        ext = self.filepath_path.split('.')
        if len(ext) > 1:
            return ext[-1]
        else:
            return ''

    def get_parent_directory(self) -> Directory:
        """
        Returns the parent directory of a file path
        """
        parent_directory = os.path.dirname(self.filepath_path)
        return Directory(parent_directory)


class SystemConfig:
    """
    Class for determining the current system and setting the correct paths.
    """
    def __init__(self):
        self.system = self.get_system()
        self.root = self.get_root()
        self.system_root = self.get_root()

    @staticmethod
    def get_system() -> System:
        """
        Returns the current system
        """

        if platform.system() == 'Darwin':
            return System.OSX
        if platform.system() == 'Windows':
            return System.WINDOWS
        if platform.system() == 'Linux':
            return System.LINUX
        else:
            return System.WINDOWS

    def get_root(self) -> str:
        """
        Returns the root path for the current system
        """
        if self.system == System.LINUX:
            return LINUX_ROOT
        if self.system == System.WINDOWS:
            return WINDOWS_ROOT
        if self.system == System.OSX:
            return OSX_ROOT
        raise ValueError('Filepath does not contain a valid system root.')
