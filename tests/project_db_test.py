from assets import imageSequence, projectFile
from core import data_manager, project, shot
from core.hutils import logger, system
from core import constants

log = logger.setup_logger()
log.debug("project_db_test.py loaded")


class ProjectDbTest:
    """
    Class for testing the project database
    """
    def __init__(self):
        constants.DB_PATH = './tests/test_db.json'
        self.db = self.create_project_db()
        self.load_projects_pass = self.load_projects()
        self.save_db_pass = self.save_db()
        self.test_create_directories()

        self.get_comps_pass = self.get_comps()
        self.get_project_files_pass = self.get_project_files()

        self.image_sequence = self.test_image_sequence()

        self.log_tests()

    @staticmethod
    @logger.timeit
    def create_project_db() -> data_manager.ProjectDataManager:
        """
        Creates a new project database
        """
        log.debug("Creating new project database")
        return data_manager.ProjectDataManager()

    @logger.timeit
    def load_projects(self) -> bool:
        """
        Loads all projects in the project database
        """
        projects = self.db.get_projects()
        has_projects = len(projects) > 0
        is_project = isinstance(projects[0], project.Project)
        has_shots = len(projects[0].get_shots()) > 0
        is_shot = isinstance(projects[0].get_shots()[0], shot.Shot)
        if has_projects and is_project and has_shots and is_shot:
            return True
        else:
            return False

    @logger.timeit
    def save_db(self):
        """
        Saves the project database
        """
        log.debug("Saving project database")
        self.db.save()

    @logger.timeit
    def get_comps(self) -> bool:
        """
        Gets all comps in the project database
        """
        example_project = self.db.get_project('wound_wood')
        example_shot = example_project.get_shot('WW_072_0040')
        comps = example_shot.get_comps()
        plates = example_shot.get_plates()

        try:
            has_comps = len(comps) > 0
            is_comp = isinstance(comps[0], imageSequence.GenericImageSequence)
            has_plates = len(plates) > 0
            is_plate = isinstance(plates[0], imageSequence.GenericImageSequence)
        except IndexError as e:
            log.error(f"IndexError: {e}")
            return False

        if has_comps and is_comp and has_plates and is_plate:
            return True
        else:
            return False

    @logger.timeit
    def get_project_files(self) -> bool:
        """
        Gets all files in the project database
        """
        example_project = self.db.get_project('wound_wood')
        example_shot = example_project.get_shot('WW_072_0040')
        files = example_shot.get_project_files()
        has_files = len(files) > 0
        try:
            is_file = isinstance(files[0], projectFile.GenericProjectFile)
        except IndexError as e:
            log.error(f"IndexError: {e}")
            return False
        if has_files and is_file:
            return True
        else:
            return False

    @logger.timeit
    def test_image_sequence(self) -> bool:
        """
        Test the image sequence class.
        :returns: bool True if successful
        """

        test_directory = system.Directory('/Users/hunterwilliams/Documents/hpipegit/tests/test_sequence')
        image_sequence = imageSequence.sequences_from_directory(test_directory)[0]
        log.info(image_sequence)
        image_sequence.to_mp4()
        return True

    @logger.timeit
    def test_create_directories(self):
        """
        Test the create directories function
        """
        example_projects = self.db.get_projects()
        for example_project in example_projects:
            data_manager.ProjectDirectoryGenerator(example_project, push_directories=True)

    def log_tests(self):
        """
        Logs the results of the tests
        """
        log.info(f"------ TESTS: Load projects: ----- {self.load_projects_pass}")
        log.info(f"------ TESTS: Save db ------------ {self.save_db_pass}")
        log.info(f"------ TESTS: Get comps ---------- {self.get_comps_pass}")
        log.info(f"------ TESTS: Get project files--- {self.get_project_files_pass}")
        log.info(f"------ TESTS: Image sequence ----- {self.image_sequence}")


if __name__ == '__main__':
    ProjectDbTest()
