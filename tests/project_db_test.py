from core import data_manager
from core.hutils import logger
from core import constants

log = logger.setup_logger()
log.debug("data_manager.py loaded")


class ProjectDbTest:
    """
    Class for testing the project database
    """
    def __init__(self):
        constants.DB_PATH = './tests/test_db.json'
        self.db = self.create_project_db()
        self.load_projects()
        self.save_db()
        self.get_comps()

    @staticmethod
    @logger.timeit
    def create_project_db() -> data_manager.ProjectDataManager:
        """
        Creates a new project database
        """
        log.debug("Creating new project database")
        return data_manager.ProjectDataManager()

    @logger.timeit
    def load_projects(self):
        """
        Loads all projects in the project database
        """
        projects = self.db.get_projects()
        log.debug(f"Loaded {len(projects)} projects")
        log.debug(f"for example, Project: {projects[3]}")
        return projects

    @logger.timeit
    def save_db(self):
        """
        Saves the project database
        """
        log.debug("Saving project database")
        self.db.save()

    @logger.timeit
    def get_comps(self):
        """
        Gets all comps in the project database
        """
        example_project = self.db.get_project('wound_wood')
        example_shot = example_project.get_shot('WW_072_0040')
        comps = example_shot.get_comps()
        log.debug(f"Loaded {comps} comps")
        return comps


if __name__ == '__main__':
    ProjectDbTest()
