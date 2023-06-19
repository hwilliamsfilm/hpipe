"""
Some customizations and basic utility functions on top of logging module.
"""
import logging
from colorlog import ColoredFormatter
from core import constants


FORMAT = "%(asctime)s::%(levelname)s-%(funcName)s | %(message)s"
LOG_LEVEL = constants.LOG_LEVEL
LOG_FORMAT = "  %(log_color)s%(levelname)-8s%(reset)s | %(log_color)s%(asctime)s:::  " \
            "%(message)s%(reset)s :: %(log_color)s%(funcName)s"


def setup_logger() -> logging.Logger:
    """
    Sets up the logger with the specified format and level and ads color from colorlog module.
    :return: logger object
    """
    logging.root.setLevel(LOG_LEVEL)
    formatter = ColoredFormatter(LOG_FORMAT)
    stream = logging.StreamHandler()
    stream.setLevel(LOG_LEVEL)
    stream.setFormatter(formatter)
    log = logging.getLogger('pythonConfig')
    log.setLevel(LOG_LEVEL)
    log.addHandler(stream)
    return log
