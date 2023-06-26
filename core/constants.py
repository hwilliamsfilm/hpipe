"""
Constants for database
"""
# from core.hutils import system
import logging
from core.hutils import system

# GENERAL CONSTANTS
LOG_LEVEL = logging.DEBUG

# General constants
PROJECTS_ROOT = system.Filepath('Y:/projects/').system_path()
ARCHIVE_ROOT = system.Filepath('Y:/projects/_archive/').system_path()

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

# PATH CONSTANTS
DB_PATH = system.Filepath(r'Y:/project_db/projects_refactor.json').system_path()
DB_BACKUP = system.Filepath(r'Y:/vault/db_backup').system_path()

# Database constants
DB_TYPE = 'json'

# LIBRARY CONSTANTS
USD_LIB = system.Filepath(r'Y:/_global_assets/usd').system_path()
#
# SHOT_FOLDER = 'shots'
# PLATE_FOLDER = 'plate'

