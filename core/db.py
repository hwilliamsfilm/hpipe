'''
Database class for current Active project datbase
'''

# Import built-in modules
from core.hutils import path, logger, errors, constants
from core import project

# Import third-party modules
import json
import shutil
import datetime
import os

# log module import
logger.imported("db.py")


class Db(object):
    """
    Database class for storing and getting project data from json file.
    """
    def __init__(self, db_path=constants.DB_PATH):
        '''
        Creates attribute location with the path and loads the data
        :param path:
        '''
        self.location = path.fix_path(db_path)
        self.data = self.load()

    # Getting things
    def get_projects(self):
        """
        Parses project objects from project json
        :return: project
        """

        from core import project

        project_list = []
        data = self.data  # changed from loading to reffing data

        # check if no projects
        if len(data.items()) == 0:
            logger.warning('No projects found')
            return False

        for key, val in data.items():
            project_list.append(project.Project.from_json(val))

        return project_list

    def get_project(self, project_name):
        """
        Wrapper function to return a single project from json
        :param project_name:
        :return: project if project exists
        """

        # iterate through projects and find specified project
        for proj in self.get_projects():
            if proj.name == project_name:
                return proj

        # if not log message and return none
        logger.warning('Project {0} not found'.format(project_name))
        return None

    def get_project_as_dict(self, proj):
        """
        same as Project() but it returns the dictionary instead of an object
        :param proj: Project Name
        :return: project as dictionary
        """
        logger.debug('Getting project dictionary...')
        data = self.data
        return data.get(proj)

    def get_data(self):
        return self.data

    # Doing things
    def load(self):
        """
        load json into data dictionary
        :return: dict() project data
        """

        logger.warning('LOADING DB')
        try:
            with open(self.location, 'r') as fileName:
                data = json.load(fileName)
            logger.debug('Loaded DB @ {0}'.format(self.location))

        except ValueError as v:
            logger.error('Cannot access db json. Please check path.')
            logger.error(v)
            data = {}

        return data

    def dump(self, data):
        """
        Dumps db data back to json file
        :param data: dict
        :return: Boole True if complete
        """

        logger.debug('Dumping new data to Project Database...')

        try:
            with open(self.location, 'w') as project_db:
                json.dump(data, project_db, sort_keys=True, indent=4)
            logger.info('Data has been dumped to DB @ {0}'.format(self.location))
            return True

        except Exception as e:
            logger.warning("Error dumping database")
            logger.warning(e)
            return False

    def update_project(self, project_name, dictionary):
        data = self.data  # changed from load
        if self.get_project(project_name):
            data[project_name] = dictionary
            self.dump(data)
            self.data = data
            return True
        return False

    def add_project(self, proj, update=False):
        """
        Adds Project to database
        :param proj:
        :param update:
        :return:
        """
        logger.debug('Adding Project to database...')

        data = self.data # changed from load
        if not update:
            if self.get_project(proj.name):
                logger.warning('Skipping {0}, project already exists'.format(proj))
                return False
        if proj:
            data[proj.name] = proj.export_project()
            self.dump(data)
            self.data = data

            proj.update_directories()

            return True
        return False

    def add_shot(self, project_name, shot, update=False):
        """
        Adds shot to project in database
        :return: Boole if executed
        """
        data = self.load()
        if not self.get_project(project_name):
            logger.warning('Project not in DB')
            return False

        if not update:
            if self.get_project(project_name).get_shot(shot.name):
                logger.warning('Skipping {0}, shot already exists'.format(shot))
                return False

        if not shot.project:
            shot.link_project(project_name)

        data[project_name]['shots'][shot.name] = shot.export()
        self.dump(data)
        logger.debug('Linked Shot {0} to Project {1}'.format(shot.name, project_name))

        self.get_project(project_name).update_directories()
        return True

    def remove_project(self, project_name, archive_dir=True):
        """
        Removes Project from Database
        :param project_name:
        :return:
        """
        projects = self.load()

        if not self.get_project(project_name):
            logger.error('Project does not exist')
            return False
        try:
            projects.pop(project_name, None)
            logger.info('REMOVED project {0} from DB'.format(project_name))
            self.dump(projects)
            return True
        except Exception as e:
            logger.error(e)
            return False

    def remove_shot(self, project_name, shot_name):
        """
        Removes shot from database.
        :param project_name:
        :param shot_name:
        :return:
        """

        projects = self.load()

        if not self.get_project(project_name):
            raise errors.ProjectNotFound(project_name)

        if not self.get_project(project_name).get_shot(shot_name):
            raise errors.ShotNotFound(shot_name)

        my_shots = projects[project_name]["shots"]
        my_shots.pop(shot_name, None)
        self.dump(projects)

        logger.info('REMOVED shot {0}'.format(shot_name))

        return True

    def add_shot_tags(self, project_name, shot_name, tags):
        """
        Adds tags to shot
        :param project_name:
        :param shot_name:
        :param tags:
        :return:
        """
        data = self.load()
        logger.warning('Adding tags to shot {0} in project {1}'.format(shot_name, project_name))
        proj = self.get_project(project_name)
        shot = proj.get_shot(shot_name)
        for tag in tags.split(','):
            shot.add_tag(tag)
        # shot.add_tags(tags)
        data[project_name]['shots'][shot.name] = shot.export()
        self.dump(data)
        return True

    def remove_all_tags(self, project_name, shot_name):
        """
        Removes all tags from shot
        :param project_name:
        :param shot_name:
        :return:
        """
        data = self.load()
        logger.warning('Removing all tags from shot {0} in project {1}'.format(shot_name, project_name))
        proj = self.get_project(project_name)
        shot = proj.get_shot(shot_name)
        shot.remove_all_tags()
        data[project_name]['shots'][shot.name] = shot.export()
        self.dump(data)
        return True

    # Utility things
    def backup_db(self):
        """
        Backs up json to backup area in case it gets corrupt at any point
        :return:
        """
        now = datetime.datetime.now()
        time = now.strftime("%Y-%m-%d__%H-%M-%S")

        db_path = self.location
        file = shutil.copy(db_path, constants.DB_BACKUP)

        new_path = path.fix_path(constants.DB_BACKUP + '/' + time + '_project_backup.json')

        os.rename(file, new_path)

        logger.info('BACKED UP TO: {0}'.format(new_path))


    # def update_directories(self):
    #     """
    #     "activates" the project - which is just adding the directories
    #     TODO: This should probably just be built into the build directories function
    #     :return:
    #     """
    #
    #     # check if project exists and create if not
    #     database = db.Db()
    #     if not database.get_project(self.name):
    #         logger.info('Adding missing project: {0}'.format(self.name))
    #         database.add_project(self)
    #
    #     # Prep project structure
    #     project_struct = db_constants.PROJECT_STRUCTURE.copy()
    #     project_struct[self.name] = project_struct['name']
    #     project_struct.pop('name', None)
    #
    #     # Get project root
    #     project_root = '{root}/{year}'.format(root=db_constants.PROJECTS_ROOT, year=self.year)
    #
    #     directory.create_directories(project_struct, project_root)
    #
    #     # Loop over shots
    #     shot_root = self.get_shot_path()
    #
    #     if self.get_shots():
    #         for s in self.get_shots():
    #             shot_struct = db_constants.SHOT_STRUCTURE.copy()
    #             shot_struct[s.name] = shot_struct['name']
    #             shot_struct.pop('name', None)
    #             directory.create_directories(shot_struct, shot_root)
    #
    #     return True