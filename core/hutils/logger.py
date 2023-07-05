"""
Some customizations and basic utility functions on top of logging module.
"""
import logging
import time
from functools import wraps

from colorlog import ColoredFormatter

FORMAT = "%(asctime)s::%(levelname)s-%(funcName)s | %(message)s"
LOG_LEVEL = logging.DEBUG
LOG_FORMAT = "  %(log_color)s%(levelname)-8s%(reset)s | %(log_color)s%(asctime)s :::  " \
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
    if logging.getLogger('pythonConfig').hasHandlers():
        logging.getLogger('pythonConfig').handlers.clear()
    log = logging.getLogger('pythonConfig')
    log.setLevel(LOG_LEVEL)
    log.addHandler(stream)
    return log


def timeit(func):
    @wraps(func)
    def timeit_wrapper(*args, **kwargs):
        log = setup_logger()
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        total_time = end_time - start_time
        log.debug(f'Function {func.__name__}{args} {kwargs} Took {total_time:.4f} seconds')
        return result, total_time

    return timeit_wrapper
