'''
Module containing logging messages for project to console
'''

from colorama import Fore
from colorama import init
import os
from core.hutils import config

init(autoreset=True)

def log(message, severity):
    '''
    Prints formatted message to console based on severity
    :param message: Message to be printed to console.
    :param severity: Severity of message to be printed.
    :return: True if executed.
    '''

    # check severity
    if severity == 'DEBUG':
        return debug(message)
    elif severity == 'INFO':
        return info(message)
    elif severity == 'WARNING':
        return warning(message)
    elif severity == 'ERROR':
        return error(message)
    else:
        return False

def debug(message):
    '''
    Prints debug formatted message if debug mode configured
    :param message: Message to be printed to console.
    :return: True if executed.
    '''

    # check config
    if config.LOGGER_DEBUG:
        print(Fore.LIGHTGREEN_EX + 'DEBUG: {0}'.format(message))
        return True
    else:
        return False


def info(message):
    '''
    Prints info formatted message if info mode configured
    :param message: Message to be printed to console.
    :return: True if executed.
    '''

    # check config
    if config.LOGGER_INFO:
        print(Fore.GREEN + 'INFO: {0}'.format(message))
        return True
    else:
        return False

def warning(message):
    '''
    Prints warning formatted message if warning mode configured
    :param message: Message to be printed to console.
    :return: True if executed.
    '''

    # check config
    if config.LOGGER_WARNING:
        print(Fore.YELLOW + 'WARNING: {0}'.format(message))
        return True
    else:
        return False


def error(message):
    '''
    Prints error formatted message if error mode configured
    :param message: Message to be printed to console.
    :return: True if executed.
    '''

    # check config
    if config.LOGGER_ERROR:
        print(Fore.RED + 'ERROR: {0}'.format(message))
        return True
    else:
        return False


def imported(message):
    """
    Prints imported formatted message
    :param message: Message to be printed to console.
    :return: True if executed.
    """

    # check config
    if config.LOGGER_IMPORT:
        print(Fore.CYAN + 'IMPORTED: {0}'.format(message))
        return True
    else:
        return False

def dict_pic(dictionary):
    """
    pprints a dictionary
    :param dictionary:
    :return:
    """

    from pprint import pprint
    pprint(dictionary)
    return True

def time(message):
    """
    Prints time formatted message if time mode configured
    :param message: str message to be printed to console.
    :return: bool True if executed.
    """
    # check config
    if config.LOGGER_TIME:
        print(Fore.MAGENTA + 'TIME: {0}'.format(message))
        return True
    else:
        return False