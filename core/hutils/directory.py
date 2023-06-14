'''
Module containing functions for building directories
'''

import os
from core.hutils import logger


def create_directories(struct_dir, root):
    '''
    Function that builds a dictionary file structure at a specified root

    :param struct_dir: dict file structure with proper names
    :param root: root path where to makedirs
    :return: Boole True if completed
    '''

    def one_directory(struct_dir, path):

        for name, info in struct_dir.items():
            myPath = path + "/" + name

            if os.path.exists(myPath):
                logger.warning('{0} skipping, already exists'.format(myPath))
                continue

            logger.info('Created: {0}'.format(myPath))
            os.makedirs(myPath)

            if isinstance(info, dict):
                one_directory(info, myPath)

    one_directory(struct_dir, root)