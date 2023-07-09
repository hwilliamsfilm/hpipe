"""
Constants for database
"""
import logging

from core.hutils import system

# LOGGING
LOG_LEVEL = logging.DEBUG

# GENERAL

# Path to the projects' root. This is where all outputs / project files / renders will be stored
PROJECTS_ROOT = system.Filepath('/Volumes/hlw01/projects').system_path()

# Path to the projects' archive root. This is where all outputs / project files / renders will be stored
# once "archived"
ARCHIVE_ROOT = system.Filepath('Y:/projects/_archive/').system_path()

# Path to the projects' recycle bin. This is where all outputs / project files / renders will be stored when any python
# script deletes a file. It's up to the user to empty this folder.
RECYCLE_BIN = system.Filepath('Y:/projects/_recycle_bin/').system_path()

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

# Names of the folders in the project root. These are used when creating a new project to create the necessary folders.
# TODO: This should be moved to the project structure dict, or at least integrated with it for more easily changing
#  the folder names.

SHOT_FOLDER = 'shots'
PLATE_FOLDER = 'plate'
OUTPUT_FOLDER = 'output'
WORKAREA_FOLDER = '_workarea'
COMP_FOLDER = 'comp'
RENDER_FOLDER = 'render'
NUKE_FOLDER = 'nuke'
WORKING_FOLDER = 'working_files'
HOUDINI_FOLDER = 'houdini'


# Default values for a new project. These are used when creating a new project to populate the project's database
FRAME_START = 1000
FRAME_END = 1100

# Base image to use as a template for generating a slate. This is part of the ImageSequence class to create deliveries.
SLATE_PATH = r'Y:\_global_assets\slate\slate_A01.png'

# Database filepath - this is where the database is stored. This is used by the Database class to load and save the
# database.
DB_PATH = system.Filepath(r'/Volumes/hlw01/project_db/projects_refactor.json').system_path()

# Database filepath - this is where the database Archive is stored. This is used by the Database class
# to load and save the archive database. Could just be the same as the DB_PATH, with a different filename.
ARCHIVE_DB_PATH = system.Filepath(r'/Volumes/hlw01/project_db/projects_refactor_archive.json').system_path()

# A folder to store backups of the database. This is used by the Database class to create backups of the database when
# it is saved or any modifications are made to it.
DB_BACKUP = system.Filepath(r'Y:/vault/db_backup').system_path()

# Database type. This is unnecessary but may be used in the future to change the database type. Currently only json is
# supported.
DB_TYPE = 'json'

