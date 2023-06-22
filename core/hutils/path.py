"""
This module contains functions for dealing with file paths.
"""

import os
import platform


def fix_path(old_path: str, seperator: str = '/') -> str:
    """
    Fixes a path to be the correct format for the current OS
    :param old_path: Path to fix
    :param seperator: Seperator to use for the path
    :return: Fixed path
    """
    _path = old_path.replace('\\', '/')
    _path = _path.replace('\\\\', '/')
    _path = _path.replace('//', '/')

    if _path.endswith('/'):
        _path = _path[:-1]

    _path = _path.replace('/', seperator)

    new_path = _path
    return new_path


class SystemConfig:
    """
    Class for determining the current system and setting the correct paths.
    """
    def __init__(self):
        self.system = get_system()
        self.root = get_root()

    @staticmethod
    def get_system(self):
        """
        Returns the current system
        """

        if platform.system() == 'Darwin':
            return 'osx'
        if platform.system() == 'Windows':
            return 'windows'
        if platform.system() == 'Linux':
            return 'linux'
        else:
            return 'windows'


def osx_to_windows(path):
    '''
    Converts osx path to windows path (specific to my server path)
    :param path: OSX path to convert
    :return: Corrected windows path
    '''
    from core.hutils import logger

    # logger.debug('Converting path to windows...')
    return fix_path('/'.join([r'Y:\\'] + path.split('/')[1:]))


def osx_to_linux(path):
    '''
    Converts osx path to linux path (specific to my server path)
    :param path: OSX path to convert
    :return: Corrected linux path
    '''
    from core.hutils import logger

    # logger.debug('Converting path to linux...')
    return fix_path('/'.join([r'/mnt/share/hlw01/'] + path.split('/')[1:]))


def windows_to_osx(path):
    '''
    Converts osx path to windows path (specific to my server path)
    :param path: OSX path to convert
    :return: Corrected windows path
    '''
    from core.hutils import logger

    # logger.debug('Converting path to osx...')
    return fix_path('/'.join([r'/Volumes/hlw01/'] + path.split('/')[1:]))


def windows_to_linux(path):
    '''
    Converts osx path to windows path (specific to my server path)
    :param path: OSX path to convert
    :return: Corrected windows path
    '''
    from core.hutils import logger

    # logger.debug('Converting path to linux...')
    return fix_path('/'.join([r'/mnt/share/hlw01/'] + path.split('/')[1:]))


def linux_to_windows(path):
    '''
    Converts osx path to windows path (specific to my server path)
    :param path: OSX path to convert
    :return: Corrected windows path
    '''
    from core.hutils import logger

    # logger.debug('Converting path to windows...')
    return fix_path('/'.join([r'Y:\\'] + path.split('/')[1:]))


def linux_to_osx(path):
    '''
    Converts osx path to windows path (specific to my server path)
    :param path: OSX path to convert
    :return: Corrected windows path
    '''
    from core.hutils import logger

    # logger.debug('Converting path to osx...')
    return fix_path('/'.join([r'/Volumes/hlw01/'] + path.split('/')[1:]))


def convertPath(path):
    '''
    Converts path to work with machine that script is being run on.
    :param path: OSX path to convert
    :return: Corrected windows path
    '''
    from core.hutils import logger

    # logger.debug('Converting path...')
    path = fix_path(path)

    machine = get_system()

    # check which OS filepath is
    if path.split('/')[0] == 'Volumes':
        # this is a apple path
        # check which OS this machine is
        if get_system() == 'windows':
            return osx_to_windows(path)
        elif get_system() == 'linux':
            return osx_to_linux(path)
        elif get_system() == 'osx':
            return path

    elif path.split('/')[0] == 'Y:':
        # this is a windows path
        # check which OS this machine is
        if get_system() == 'osx':
            return windows_to_osx(path)
        elif get_system() == 'linux':
            return windows_to_linux(path)
        elif get_system() == 'windows':
            return path

    elif path.split('/')[0] == 'mnt':
        # this is a linux path
        # check which OS this machine is
        if get_system() == 'osx':
            return linux_to_osx(path)
        elif get_system() == 'windows':
            return linux_to_windows(path)
        elif get_system() == 'linux':
            return path


def relative_path(path):
    '''
    returns relative path for any input path
    :param path:
    :return:
    '''

    if get_system() == 'windows':
        return fix_path('/'.join(path.split('/')[2:]))
    if get_system() == 'osx':
        return fix_path('/'.join(path.split('/')[3:]))


def get_extension(path):
    '''
    returns extension for given filepath
    :param path:
    :return:
    '''

    ext = path.split('.')

    if len(ext) > 1:
        return ext[-1]
    else:
        return None


def verify_directory(directory, create_if_not=False, verbose=False):
    """
    Checks if directory exists, if not, can optionally create it.
    :param directory: str directory to check
    :param create_if_not: bool create directory if it doesn't exist
    :param verbose: bool print out info
    :return: str directory path
    """
    # fix path
    directory = fix_path(directory)

    # check if directory exists
    if not os.path.exists(directory):
        # if not, check if we should create it
        if create_if_not:
            # create directory
            os.makedirs(directory)
        else:
            # otherwise, raise error if verbose
            if verbose:
                raise IOError('Directory does not exist: %s' % directory)
            else:
                return None

    else:
        # if directory exists, return it
        return directory
