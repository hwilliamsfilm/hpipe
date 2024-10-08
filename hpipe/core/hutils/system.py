"""
This module contains functions for dealing with file paths.
"""
import os
import platform
from enum import Enum
from typing import *
import datetime

from hpipe.core.hutils import path

LINUX_ROOT = r'/mnt/share/hlw01/'
WINDOWS_ROOT = r'Y:/'
OSX_ROOT = r'/Volumes/hlw01/'
LOCAL_ROOT = os.path.expanduser('~')


class System(Enum):
    OSX = 'osx'
    WINDOWS = 'windows'
    LINUX = 'linux'
    RELATIVE = 'relative'
    LOCAL = 'local'


class Directory:
    """
    Base class for a directory on disk. This class is meant to be very generic and only describe the most basic
    properties of a directory. It is meant to be subclassed to create more specific directory types.
    """
    def __init__(self, directory_path: str, directory_name: str = '', force_raw_path: bool = False):
        self.force_raw_path = force_raw_path
        self.directory_path = path.fix_path(directory_path)
        if directory_name == '':
            directory_name = os.path.basename(directory_path)
        self.directory_path = self.system_path()
        self.directory_name = directory_name

    def __repr__(self):
        return f'Directory({self.directory_path})'

    def get_files(self) -> List['Filepath']:
        """
        Returns a list of all files in the directory.
        """
        directory_files: list[Filepath] = []
        for root, dirs, files in os.walk(self.directory_path):
            for file in files:
                directory_files.append(Filepath(os.path.join(root, file)))

        return directory_files

    def get_files_by_extension(self, extension: str, recurse=True) -> List['Filepath']:
        """
        Returns a list of all files in the directory with the given extension.
        """
        directory_files: list[Filepath] = []

        if recurse:
            for root, dirs, files in os.walk(self.directory_path):
                for file in files:
                    if file.endswith(extension):
                        directory_files.append(Filepath(os.path.join(root, file)))

        else:
            for file in os.listdir(self.directory_path):
                if file.endswith(extension):
                    directory_files.append(Filepath(os.path.join(self.directory_path, file)))

        return directory_files

    def get_parent_directory(self) -> 'Directory':
        """
        Returns a new directory object representing the parent directory of this one if it exists.
        """
        return Directory('/'.join(self.directory_path.split('/')[:-1]))

    def get_basename(self) -> str:
        """
        Returns the basename of the directory.
        """
        return os.path.basename(self.directory_path)

    def get_subdirectories(self) -> List['Directory']:
        """
        Returns a list of all subdirectories in the directory.
        :return: list of subdirectories
        """
        subdirectories: list[Directory] = []
        for root, dirs, files in os.walk(self.directory_path):
            for directory in dirs:
                subdirectories.append(Directory(os.path.join(root, directory)))
        return subdirectories

    def get_children_directories(self) -> List['Directory']:
        """
        Returns a list of all subdirectories in the directory. Does not recurse.
        :return: list of subdirectories
        """
        subdirectories: list[Directory] = []
        for f in os.listdir(self.directory_path):
            if os.path.isdir(os.path.join(self.directory_path, f)):
                subdirectories.append(Directory(os.path.join(self.directory_path, f)))
        return subdirectories

    def system_path(self) -> str:
        """
        Returns the system path of the directory.
        """
        self.directory_path = Filepath(self.directory_path, force_raw_path=self.force_raw_path).system_path()
        return self.directory_path

    def exists(self) -> bool:
        """
        Returns True if the directory exists, False if not.
        """
        return os.path.exists(self.directory_path)


class Filepath:
    """
    Base class for a filepath. This class is meant to be very generic and only describe the most basic
    properties of a filepath. It is meant to be subclassed to create more specific filepath types, like images,
    project files, etc.
    """

    def __init__(self, filepath_path: str, filepath_name: str = '', force_raw_path: bool = False):
        self.force_raw_path = force_raw_path
        self.filepath_path = path.fix_path(filepath_path)
        self.filepath_path = self.expand_path()
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

        projectfile_extension = ['nk', 'nc', 'hip', 'hipnc', 'hiplc']
        if self.get_extension() in projectfile_extension:
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

        # TODO logic needs to be reworked
        if LINUX_ROOT in self.filepath_path:
            return System.LINUX
        if WINDOWS_ROOT in self.filepath_path:
            return System.WINDOWS
        if r"C:" in self.filepath_path:
            return System.WINDOWS
        if OSX_ROOT in self.filepath_path:
            return System.OSX
        if "/Users" in self.filepath_path:
            # FIXME: This assumes that only osx uses /users for local storage
            #       which is most likely incorrect
            return System.OSX

        # FIXME: This is a hacky way to check if the path is relative
        if self.filepath_path == '.' or self.filepath_path == r'./':
            return System.RELATIVE

        raise ValueError(f'Filepath: {self.filepath_path} does not contain a valid system root.')

    def expand_path(self) -> str:
        """
        Expands the path to the current system if there is a ~ in the path.
        """
        if '~' in self.filepath_path:
            self.filepath_path = self.filepath_path.replace('~', SystemConfig.get_home())
        return self.filepath_path

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
        if self.system == System.RELATIVE:
            return ''
        raise ValueError('Filepath does not contain a valid system root.')

    def system_path(self) -> str:
        """
        Returns the path for the current system
        """
        sys_config = SystemConfig()
        environment = sys_config.system

        if self.force_raw_path:
            return self.filepath_path

        if '~' in self.filepath_path:
            self.filepath_path.replace('~', sys_config.get_home())

        if environment != self.system and self.system != System.RELATIVE:
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

    def get_filename(self) -> str:
        """
        Returns the filename of a file path
        """
        if self.has_frame_number():
            return '_'.join(os.path.basename(self.filepath_path).split('.')[0].split('_')[:-1])
        return os.path.basename(self.filepath_path).split('.')[0]

    def exists(self) -> bool:
        """
        Returns True if the filepath exists, False if not
        """
        return os.path.exists(self.filepath_path)


def path_factory(filepath: str) -> Union[Filepath, Directory]:
    """
    Factory function for creating a path object. This function will return a Directory object if the filepath
    is a directory and a Filepath object if the filepath is a file.
    :param filepath: filepath to create an object from
    :return: Filepath or Directory object
    """
    if os.path.isdir(filepath):
        return Directory(filepath)
    else:
        return Filepath(filepath)


class SystemConfig:
    """
    Class for determining the current system and setting the correct paths.
    """
    def __init__(self):
        self.system = self.get_system()
        self.root = self.get_root()
        self.system_root = self.get_root()

    @staticmethod
    def get_system_date() -> str:
        """
        Returns the current date in the format: YYYY_MM_DD
        """
        return datetime.datetime.now().strftime('%Y_%m_%d')

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

    @staticmethod
    def get_home() -> str:
        """
        Returns the home directory for the current system.
        """
        return os.path.expanduser('~')

