from assets import imageSequence, projectFile
from core import constants, data_manager, project, shot
from core.hutils import logger, system

log = logger.setup_logger()
log.debug("project_db_test.py loaded")


class ProjectDbTest:
    """
    Class for testing the project database
    """
    def __init__(self):
        constants.DB_PATH = './tests/test_db.json'
        self.db = self.create_project_db()[0]
        self.load_projects_pass = self.load_projects()
        self.save_db_pass = self.save_db()

        self.create_project = self.test_create_project()
        self.remove_project = self.test_remove_project()

        self.test_create_directories()

        self.get_comps_pass = self.get_comps()
        self.get_project_files_pass = self.get_project_files()

        self.image_sequence = self.test_image_sequence()

        self.test_archive = self.test_archive_project()
        self.test_unarchive = self.test_unarchive_project()

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
        try:
            self.db.save()
        except Exception as e:
            log.error(f"Exception: {e}")
            return False
        return True

    @logger.timeit
    def test_create_project(self):
        """
        Creates a new project
        """
        log.debug("Creating new project")
        new_project = project.Project('test_project', description='test_project: this is'
                                                                  'created as a test during testing')
        self.db.add_project(new_project, push=True)

        if not self.db.is_project('test_project'):
            return False

        return True

    @logger.timeit
    def test_remove_project(self):
        """
        Removes a project
        """
        log.debug("Removing project")
        example_project = self.db.get_project('test_project')
        self.db.remove_project(example_project, push=True)

        if self.db.is_project('test_project'):
            return False

        return True

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

    @logger.timeit
    def test_archive_project(self):
        """
        Test the archive project function
        """
        example_project = self.db.get_project('wound_wood')
        self.db.archive_project(example_project)
        return True

    @logger.timeit
    def test_unarchive_project(self):
        example_project = self.db.get_archive_project('wound_wood')
        self.db.unarchive_project(example_project)
        return True

    def log_tests(self):
        """
        Logs the results of the tests
        """
        log.info(f"------ TESTS: Load projects: ----- {self.load_projects_pass[0]} -> {self.load_projects_pass[1]}")
        log.info(f"------ TESTS: Save db ------------ {self.save_db_pass[0]} -> {self.save_db_pass[1]}")
        log.info(f"------ TESTS: Create project ----- {self.create_project[0]} -> {self.create_project[1]}")
        log.info(f"------ TESTS: Remove project ----- {self.remove_project[0]} -> {self.remove_project[1]}")
        log.info(f"------ TESTS: Get comps ---------- {self.get_comps_pass[0]} -> {self.get_comps_pass[1]}")
        log.info(f"------ TESTS: Get project files--- {self.get_project_files_pass[0]} -> {self.get_project_files_pass[1]}")
        log.info(f"------ TESTS: Image sequence ----- {self.image_sequence[0]} -> {self.image_sequence[1]}")
        log.info(f"------ TESTS: Archive project ---- {self.test_archive[0]} -> {self.test_archive[1]}")
        log.info(f"------ TESTS: Unarchive project -- {self.test_unarchive[0]} ->  {self.test_unarchive[1]}")


if __name__ == '__main__':
    ProjectDbTest()
