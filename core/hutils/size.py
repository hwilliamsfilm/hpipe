import os
from core.hutils import logger


def get_size(path):
    '''
    Computes the size of directory
    :return: size in MB
    '''
    if os.path.isdir(path):
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                # skip if it is symbolic link
                if not os.path.islink(fp):
                    # logger.debug(fp)
                    total_size += os.path.getsize(fp)
        size = total_size / 1024 / 1024
        logger.debug(size)
        return size
    else:
        size = os.path.getsize(path) / 1024 / 1024
        logger.debug(size)
        return size
