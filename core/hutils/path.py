'''
Module containing path core.hutils functions
'''

import os
import platform
import re
from core.hutils import logger
from pprint import pprint


def fix_path(old_path, sep='/'):
    '''
    Returns corrected path
    :param old_path: path to fix
    :param sep: seperator for new path
    :return: Str corrected path
    '''

    _path = old_path.replace('\\', '/')
    _path = _path.replace('\\\\', '/')
    _path = _path.replace('//', '/')

    if _path.endswith('/'):
        _path = _path[:-1]

    _path = _path.replace('/', sep)

    new_path = _path
    return new_path


def get_system():
    '''
    Returns "osx" or "windows" depending on where this function is run
    :return: str "osx" or "windows"
    '''
    from core.hutils import logger

    if platform.system() == 'Darwin':
        # logger.debug('OSX MACHINE')
        return 'osx'
    if platform.system() == 'Windows':
        # logger.debug('WINDOWS MACHINE')
        return 'windows'
    if platform.system() == 'Linux':
        # logger.debug('LINUX MACHINE')
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


def get_image_sequences(dir):
    '''
    Takes a directory argument and returns a dictionary of filenames (keys) and list of frames (values)
    :param dir:
    :return:
    '''
    from asset import sequence

    regex = r'(?P<root>.+)/(?P<filename>.+)_(?P<frame>\d+).(?P<extension>\w+)'
    filenames = {}

    for d in os.listdir(dir):
        # logger.debug(d)
        full_path = dir+'/'+d
        match = re.match(regex, full_path, flags=re.IGNORECASE)
        if match:
            if get_extension(d)=='txt':
                continue
            if get_extension(d)=='tx':
                continue
            if get_extension(d)=='mp4':
                continue
            name = match.group('filename')
            if name in filenames.keys():
                filenames[name].append(full_path)
            else:
                filenames[name] = [full_path]

    for k, v in filenames.items():
        v.sort()
        filenames[k] = v

    # logger.debug(filenames)

    sequences = []
    for k, v in filenames.items():
        if 'deep' in k:
            continue
        if get_extension(v[0]) == 'exr':
            sequences.append(sequence.ExrImageSequence(v))
        if get_extension(v[0]) == 'jpg' or get_extension(v[0]) == 'png':
            sequences.append(sequence.GeneralImageSequence(v))

    return sequences


def get_image_dirs(root):
    sequences = []
    for folder in os.listdir(root):
        # logger.debug(folder)
        d = root + '/' + folder
        try:
            image_seq = get_image_sequences(d)
            # logger.debug(d)
            if image_seq:
                sequences.append(image_seq[0])
        except NotADirectoryError as e:
            logger.debug('skipping {0}'.format(d))

    return sequences


def roundrobin(*iterables):
    """
    roundrobin('ABC', 'D', 'EF') --> A D E B F C
    """
    from itertools import cycle, islice
    # Recipe credited to George Sakkis
    num_active = len(iterables)
    nexts = cycle(iter(it).__next__ for it in iterables)
    while num_active:
        try:
            for next in nexts:
                yield next()
        except StopIteration:
            # Remove the iterator we just exhausted from the cycle.
            num_active -= 1
            nexts = cycle(islice(nexts, num_active))
