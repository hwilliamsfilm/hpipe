"""
Startup script to configure the pipe environment and get user preferences.
"""

# need to get information about this:
# LINUX_ROOT = r'/mnt/share/hlw01/'
# WINDOWS_ROOT = r'Y:/'
# OSX_ROOT = r'/Volumes/hlw01/'
# LOCAL_ROOT = os.path.expanduser('~')



# "PROJECTS_ROOT": "/Users/hunterwilliams/Documents/projects/", quick
# "ASSETS_ROOT": "/Users/hunterwilliams/Documents/_global_assets/assets/", quick
# "RECYCLE_BIN": "/Users/hunterwilliams/Documents/projects/_recycle_bin/", quick
# "DB_PATH": "/Users/hunterwilliams/Documents/project_db/projects.json", quick
# "ARCHIVE_DB_PATH": "/Users/hunterwilliams/Documents/project_db/projects_archive.json", quick
# "DB_BACKUP": "/Users/hunterwilliams/Documents/vault/db_backup/", quick
# "DB_TYPE": "json", quick
# "GLOBAL_ASSETS": "/Users/hunterwilliams/Documents/_global_assets/", quick
# "ASSET_DB_PATH": "/Users/hunterwilliams/Documents/project_db/assets.json", quick
# "HPIPE_PATH": "/Users/hunterwilliams/Documents/project_db/", quick
# "BETA": "False" quick
# Houdini environment file
# .nuke folder

# TODO need to figure out a way to store these in a much more performant way throughout the code. I dont think its
# very efficient to be calling the configuration manager in a ton of areas

class SetupConfiguredEnvironment:
    """
    Class object that represents the user's configured environment.
    """
    def __init__(self):
        self.quick_install = self.ask_quick_install()

        if self.ask_network_drive():
            self.windows_root = self.ask_windows_root()
            self.linux_root = self.ask_linux_root()
            self.osx_root = self.ask_osx_root()

        if not self.quick_install:
            self.project_root_directory = self.ask_project_root_directory()
            self.asset_root_directory = self.ask_asset_root_directory()
            self.database_direcotry = self.ask_database_file_direcotry()
            self.global_assets_directory = self.ask_global_assets_directory()

        if not self.find_houdini_preferences():
            self.houdini_prefernces = self.ask_houdini_preferences()
        if not self.find_nuke_preferences():
            self.nuke_preferences = self.ask_nuke_preferences()

        self.modify_houdini_env()
        self.modify_nuke_env()

    def ask_quick_install(self):
        """
        Ask the user if they want to do a custom install or a quick one that uses a single directory path.
        """
        message = ("Do you want to quick install with one directory? If no, you will need to manually choose "
                   " multiple file/directory paths (y/n) ")

        if input(message).lower() == 'y':
            return True
        else:
            return False

    def ask_directory(self):
        """
        Ask the user for the project directory.
        """
        raise NotImplementedError

    def ask_linux_root(self):
        """
        Ask the user if they have a linux root.
        """
        linux_bool = input('Do you have a linux machine? (y/n) ')
        if linux_bool.lower() == 'y':
            return True
        else:
            return False

    def ask_windows_root(self):
        """
        Ask the user if they have a windows root.
        """
        windows_bool = input('Do you have a windows machine? (y/n) ')
        if windows_bool.lower() == 'y':
            return True
        else:
            return False


