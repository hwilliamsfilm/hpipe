import os
from core.hutils import logger, system
from assets import asset
from abc import ABC, abstractmethod

from typing import *
if TYPE_CHECKING:
    pass

log = logger.setup_logger()
log.debug("ImageSequence.py loaded")


class GenericImageSequence(asset.Asset):
    """
    Class for an image sequence. Stores related images as a list of filepaths.
    """
    def __init__(self, filepaths: list['system.Filepath'], asset_name: str = '',
                 start_frame: int = 0, end_frame: int = 0):
        super().__init__(asset_name)

        if start_frame == 0:
            start_frame = self.get_start_frame()

        if end_frame == 0:
            end_frame = self.get_end_frame()

        self.start_frame = start_frame
        self.end_frame = end_frame
        self.filepaths = filepaths

    def __repr__(self) -> str:
        return f"ImageSequence <{self.asset_name}> from <{self.get_parent_directory().directory_path}>"

    def get_start_frame(self) -> int:
        pass

    def get_end_frame(self) -> int:
        pass

    def get_total_frames(self) -> int:
        pass

    def get_parent_directory(self) -> 'asset.Directory':
        """
        Returns the parent directory of the image sequence.
        """
        return self.filepaths[0].get_parent_directory()


class ExrImageSequence(GenericImageSequence):
    """
    Class for an exr image sequence. Stores related images as a list of filepaths.
    """
    def __init__(self, filepaths: list['system.Filepath'], asset_name: str = '',
                 start_frame: int = 0, end_frame: int = 0):
        super().__init__(filepaths, asset_name, start_frame, end_frame)

    def __repr__(self):
        return f"ExrImageSequence <{self.asset_name}> from <{self.get_parent_directory().directory_path}>"


class JpgImageSequence(GenericImageSequence):
    """
    Class for a jpg image sequence. Stores related images as a list of filepaths.
    """
    def __init__(self, filepaths: list['system.Filepath'], asset_name: str = '',
                 start_frame: int = 0, end_frame: int = 0):
        super().__init__(filepaths, asset_name, start_frame, end_frame)

    def __repr__(self):
        return f"JpgImageSequence <{self.asset_name}> from <{self.get_parent_directory().directory_path}>"


class PngImageSequence(GenericImageSequence):
    """
    Class for a png image sequence. Stores related images as a list of filepaths.
    """
    def __init__(self, filepaths: list['system.Filepath'], asset_name: str = '',
                 start_frame: int = 0, end_frame: int = 0):
        super().__init__(filepaths, asset_name, start_frame, end_frame)

    def __repr__(self):
        return f"PngImageSequence <{self.asset_name}> from <{self.get_parent_directory().directory_path}>"


def sequence_factory(file_paths: list['system.Filepath'], file_name: str = '') -> GenericImageSequence:
    """
    Factory function for creating image sequences from a list of filepaths.
    :param file_paths: List of filepaths
    :param file_name: Name of the image sequence
    :return: Image sequence
    """
    file_path_extension = file_paths[0].get_extension()
    if file_path_extension == 'exr':
        return ExrImageSequence(file_paths, file_name)
    elif file_path_extension == 'jpg':
        return JpgImageSequence(file_paths, file_name)
    elif file_path_extension == 'png':
        return PngImageSequence(file_paths, file_name)
    else:
        raise ValueError(f"Could not create image sequence from {file_paths}.")


def sequences_from_directory(directory: asset.Directory) -> list[GenericImageSequence]:
    """
    Returns a list of image sequences from a directory.
    :param directory: Directory to search for image sequences
    :return: List of image sequences
    """
    log.debug(directory.directory_path)
    directory_sequences = []

    for sub_directory in os.listdir(directory.directory_path):
        sub_directory_sequences = []
        sub_directory = os.path.join(directory.directory_path, sub_directory)

        if not os.path.isdir(sub_directory):
            log.warning(f"{sub_directory} is not a directory. Skipping..")
            continue

        has_files = len(os.listdir(sub_directory)) > 0
        if not has_files:
            log.warning(f"{sub_directory} is empty. Skipping..")
            continue

        sequences_dictionary: dict[str, list[system.Filepath]] = {}
        for root, dirs, files in os.walk(sub_directory):
            for file in files:
                basename = '_'.join(file.split('_')[:-1])
                full_path = os.path.join(root, file)

                if full_path == '' or full_path is None:
                    log.warning(f"Could not find full path for {file}. Skipping..")
                    continue

                if system.Filepath(full_path).get_extension() not in ['exr', 'jpg', 'png']:
                    log.warning(f"{file} is not a valid image file. Skipping..")
                    continue

                if basename not in sequences_dictionary:
                    sequences_dictionary[basename] = []
                    sequences_dictionary[basename].append(system.Filepath(full_path))
                else:
                    sequences_dictionary[basename].append(system.Filepath(full_path))

        for sequence_key, sequence_value in sequences_dictionary.items():
            sub_directory_sequences.append(sequence_factory(sequence_value, sequence_key))

        log.debug(f"Found {len(sub_directory_sequences)} sequences in {sub_directory}")
        directory_sequences.extend(sub_directory_sequences)

    log.info(f"Found {len(directory_sequences)} sequences in {directory.directory_path}")
    return directory_sequences

