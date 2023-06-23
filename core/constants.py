"""
Constants for database
"""
from core.hutils import system
import logging

# GENERAL CONSTANTS
LOG_LEVEL = logging.DEBUG

# General constants
PROJECTS_ROOT = path.convertPath('Y:/projects/')
ARCHIVE_ROOT = path.convertPath('Y:/projects/_archive/')

# Directory structure
PROJECT_STRUCTURE = {
    "name": {
        "_assets": None,
        "hda": None,
        "shots": None,
        "scripts": None,
        "deliveries": None
    }
}

SHOT_STRUCTURE = {
    "name":{
        "output": {
            "_workarea": None,
            "cache": None,
            "render": None,
            "comp": None,
        },
        "working_files": {
            "houdini": None,
            "nuke": None,
            "misc": None,
        },
        "plate": None,
        "ref": None,
        "trak": None
    }
}


'''
Constants / defaults for Shot Class
'''

FRAME_START = 1000
FRAME_END = 1100

SLATE_PATH = r'Y:\_global_assets\slate\slate_A01.png'

SHOT_FOLDER = 'shots'
PLATE_FOLDER = 'plate'
OUTPUT_FOLDER = 'output'
WORKAREA_FOLDER = '_workarea'
COMP_FOLDER = 'comp'
RENDER_FOLDER = 'render'
NUKE_FOLDER = 'nuke'
WORKING_FOLDER = 'working_files'

from core.hutils import system

# PATH CONSTANTS
DB_PATH = path.convertPath(path.fix_path(r'Y:/project_db/projects_refactor.json'))
DB_BACKUP = path.convertPath(path.fix_path(r'Y:/vault/db_backup'))

# Database constants
DB_TYPE = 'json'

# LIBRARY CONSTANTS
USD_LIB = path.convertPath(path.fix_path(r'Y:/_global_assets/usd'))

SHOT_FOLDER = 'shots'
PLATE_FOLDER = 'plate'


