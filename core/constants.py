"""
Constants for database
"""
import logging

from core.hutils import system

# LOGGING
LOG_LEVEL = logging.DEBUG

# GENERAL

LOCAL_TESTING = True

# Directory structure for a project. This is used when creating a new project to create the necessary folders.
# Would need to know the code intimately to change this as it would require some modifications to the projects' and
# shot classes.
PROJECT_STRUCTURE = {
    "name": {
        "_assets": '',
        "hda": '',
        "shots": '',
        "scripts": '',
        "deliveries": ''
    }
}

# Directory structure for a shot. This is used when creating a new shot to create the necessary folders. Like the
# project structure, this would require some intimate knowledge of the code to change.
SHOT_STRUCTURE = {
    "name": {
        "output": {
            "_workarea": '',
            "cache": '',
            "render": '',
            "comp": '',
            "usd": '',
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

ASSET_STRUCTURE = {
    "name": {
        "thumbnail": '',
        "notes": '',
        "asset_root": '',
        "preview": '',
    }
}


# Names of the folders in the project root. These are used when creating a new project to create the necessary folders.
# TODO: This should be moved to the project structure dict, or at least integrated with it for more easily changing
#  the folder names.

SHOT_FOLDER = 'shots'
PLATE_FOLDER = 'plate'
OUTPUT_FOLDER = 'output'
WORKAREA_FOLDER = '_workarea'
COMP_FOLDER = 'comp'
RENDER_FOLDER = 'render'
CACHE_FOLDER = 'cache'
NUKE_FOLDER = 'nuke'
USD_FOLDER = 'usd'
WORKING_FOLDER = 'working_files'
HOUDINI_FOLDER = 'houdini'
PROJECTS_DIR_NAME = 'projects'
USD_FILE_NAME = 'shot.usda'


# Default values for a new project. These are used when creating a new project to populate the project's database
FRAME_START = 1000
FRAME_END = 1100

# get home directory:
CONFIG_PATH = system.Filepath(r'~/hpipe_config.json').system_path()

# Set default SHOT usd hierarchy:
USD_HIERARCHY = {
    'meta': {},
    'world': {
        'env': {},
        'chr': {},
        'prp': {},
        'camera': {},
        'light': {},
        'fx': {},
        'misc': {},
    }
}

SHOT_USD_LAYERS = ['layout',
                   'anim',
                   'fx',
                   'light',
                   'render']

