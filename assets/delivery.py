"""
class representing a delivery package
"""

import os
import shutil
import datetime
from core import db
from core.hutils import logger
from core.hutils import path

def _get_project_and_shot_name(filepath):
    """
    Gets the project and shot name from a filepath
    :param filepath:
    :return:
    """

    # Split the filepath into components
    components = filepath.split(os.path.sep)

    # Find the index of the 'shots' directory
    shots_index = components.index('shots')

    # Extract the project and shot names
    project_name = components[shots_index - 1]
    shot_name = components[shots_index + 1]

    return (project_name, shot_name)

class Delivery():
    """
    Class representing a delivery package
    """

    # init
    def __init__(self, directory):
        self.directory = directory
        self.name = os.path.basename(directory)
        self.date = datetime.datetime.fromtimestamp(os.path.getmtime(directory))

        self.project = None
        self.shot = None
        self.delivery_types = []

        # startup verification process
        self.get_shot_information()
        self.get_delivery_types()
        self.create_log()

        # perform verification and archive
        self.get_plate()
        self.get_project_files()
        self.validate_files()

        self.copy_dependencies()

    # methods

    def get_shot_information(self):
        """
        Gets the shot information from the delivery directory
        """
        # get the project at /projects/project_name
        from db import db
        database = db.Db()
        project_name, shot_name = _get_project_and_shot_name(self.directory)
        self.project = database.get_project(project_name)
        self.shot = self.project.get_shot(shot_name)
        self.frame_start = int(self.shot.frame_start)
        self.frame_end = int(self.shot.frame_end)
        self.total_frames = self.frame_end - self.frame_start + 1
        self.total_time = self.total_frames / 24.0

        logger.info('Project: {0}'.format(self.project))
        logger.info('Shot: {0}'.format(self.shot))
        logger.info('Frame Range: {0}-{1}'.format(self.frame_start, self.frame_end))
        logger.info('Total Frames: {0}'.format(self.total_frames))
        logger.info('Total Time: {0}'.format(self.total_time))
        return True

    def get_delivery_types(self):
        for dir in os.listdir(self.directory):
            if 'mov' in dir:
                self.delivery_types.append('mov')
            elif 'exr' in dir:
                self.delivery_types.append('exr')
            elif 'jpg' in dir:
                self.delivery_types.append('jpg')
            elif 'png' in dir:
                self.delivery_types.append('png')
        logger.info('Delivery Types: {0}'.format(self.delivery_types))
        return True

    def get_plate(self):
        plate_path = self.shot.get_plate_path()
        for plate in os.listdir(plate_path):
            if 'ref' in plate:
                self.plate = True
                self.plate_path = plate_path + plate
                logger.info('Plate: {0}'.format(self.plate_path))
                return plate_path + plate

    def get_project_files(self):
        project_files = []
        for file in self.shot.get_project_files():
            project_files.append(file.get_filepath())
        self.project_files = project_files
        logger.info('Project Files: {0}'.format(self.project_files))
        return True

    def validate_files(self):
        with open(self.log_file, 'a') as f:
            f.write('####################\n')
            f.write('VALIDATING FILES\n')
            f.write('####################\n')
        for type in self.delivery_types:
            if type == 'mov':
                import ffmpeg
                from pprint import pprint
                import json
                mov = os.listdir(os.path.join(self.directory, type))[0]
                mov_path = os.path.join(self.directory, type, mov)
                info = ffmpeg.probe(mov_path)

                # record info to log file
                with open(self.log_file, 'a') as f:
                    f.write('MOV FILE: {0}\n'.format(mov_path))
                    f.write('MOV INFO:\n')
                    f.write(json.dumps(info, indent=4))
                    f.write('\n')

                size = os.path.getsize(os.path.join(self.directory, type))
                size_string = '{0} MB'.format(round(size / 1000000.0, 2))
                with open(self.log_file, 'a') as f:
                    f.write('FOUND MOV FILE: {0} WITH SIZE: {1}\n'.format(os.path.join(self.directory, type), size_string))
                continue
            directory = os.path.join(self.directory, type)

            for file in os.listdir(directory):
                filepath = os.path.join(directory, file)
                filepath= path.fix_path(filepath)
                size = os.path.getsize(filepath)
                size_string = '{0} MB'.format(round(size / 1000000.0, 2))
                if 'temp' in file:
                    logger.warning('Temp file found: {0}'.format(file))
                # add filename to log file
                with open(self.log_file, 'a') as f:
                    f.write(filepath + '            SIZE: {0}\n'.format(size_string))
            length = len(os.listdir(directory))
            if length == self.total_frames:
                logger.info('All frames accounted for')
                with open(self.log_file, 'a') as f:
                    f.write('TOTAL FRAMES: {0}\n'.format(length))
                    f.write('All frames accounted for\n')

            else:
                logger.warning('Missing frames')
                raise Exception('Missing frames at {0}'.format(directory))


    def create_log(self):
        """
        Creates a log file in the delivery directory
        """
        log_file = os.path.join(self.directory, 'log.txt')
        with open(log_file, 'w') as f:
            f.write('Delivery created on {0}\n'.format(self.date))
            # write project and shot information
            project_line = 'Project: {0}'.format(self.project)
            shot_line = 'Shot: {0}'.format(self.shot)
            frame_range = 'Frame Range: {0}-{1}'.format(self.frame_start, self.frame_end)
            total_frames = 'Total Frames: {0}'.format(self.total_frames)
            total_time = 'Total Time: {0}'.format(self.total_time)
            delivery_types = 'Delivery Types: {0}'.format(self.delivery_types)
            f.write(project_line + '\n')
            f.write(shot_line + '\n')
            f.write(frame_range + '\n')
            f.write(total_frames + '\n')
            f.write(total_time + '\n')
            f.write(delivery_types + '\n')
            f.write('####################\n\n\n')


        self.log_file = log_file

    def copy_dependencies(self):
        """
        Copies the dependencies to the delivery directory
        """
        # create a dependencies directory
        dependencies_directory = os.path.join(self.directory, '_dependencies')
        # create project files subdirectory
        project_files_directory = os.path.join(dependencies_directory, 'project_files')
        # create plate subdirectory
        plate_directory = os.path.join(dependencies_directory, 'plate')
        # copy project files
        logger.info('Copying project files to {0}'.format(project_files_directory))
        logger.info('Project Files: {0}'.format(self.project_files))

        for directory in [dependencies_directory, project_files_directory]:
            if not os.path.exists(directory):
                os.mkdir(directory)

        for file in self.project_files:
            shutil.copy(file, project_files_directory)
            with open(self.log_file, 'a') as f:
                f.write('Copied project file: {0}\n'.format(file))
        # copy plate
        if self.plate:
            # copy directory
            shutil.copytree(self.plate_path, plate_directory)
            with open(self.log_file, 'a') as f:
                f.write('Copied plate: {0}\n'.format(self.plate_path))
        return True

