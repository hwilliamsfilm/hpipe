"""
Constants for database
"""
# from core.hutils import system
import logging

from core.hutils import system

# GENERAL CONSTANTS
LOG_LEVEL = logging.DEBUG

# General constants
PROJECTS_ROOT = system.Filepath('/Volumes/hlw01/projects').system_path()
ARCHIVE_ROOT = system.Filepath('Y:/projects/_archive/').system_path()
RECYCLE_BIN = system.Filepath('Y:/projects/_recycle_bin/').system_path()

# Directory structure
PROJECT_STRUCTURE = {
    "name": {
        "_assets": '',
        "hda": '',
        "shots": '',
        "scripts": '',
        "deliveries": ''
    }
}

SHOT_STRUCTURE = {
    "name": {
        "output": {
            "_workarea": '',
            "cache": '',
            "render": '',
            "comp": '',
        },
        "working_files": {
            "houdini": '',
            "nuke": '',
            "misc": '',
        },
        "plate": '',
        "ref": '',
        "trak": ''
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
HOUDINI_FOLDER = 'houdini'

# PATH CONSTANTS
DB_PATH = system.Filepath(r'/Volumes/hlw01/project_db/projects_refactor.json').system_path()
ARCHIVE_DB_PATH = system.Filepath(r'/Volumes/hlw01/project_db/projects_refactor_archive.json').system_path()
DB_BACKUP = system.Filepath(r'Y:/vault/db_backup').system_path()

# Database constants
DB_TYPE = 'json'

# LIBRARY CONSTANTS
USD_LIB = system.Filepath(r'Y:/_global_assets/usd').system_path()
#
# SHOT_FOLDER = 'shots'
# PLATE_FOLDER = 'plate'

