from core.hutils import logger
import time


def timing_decorator(func):
    """
    Decorator that times the execution of a function
    :param func: Function to time
    :return: the function
    """
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        logger.time(f"Execution time of {func.__name__}: {execution_time} seconds")
        return result
    return wrapper
