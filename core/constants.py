"""
Constants for database
"""
from core.hutils import path
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