from core.hutils import logger, path
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
    def __init__(self, filepaths: list['asset.Filepath'], asset_name: str = '',
                 start_frame: int = 0, end_frame: int = 0):
        super().__init__(asset_name)

        if start_frame == 0:
            start_frame = self.get_start_frame()

        if end_frame == 0:
            end_frame = self.get_end_frame()

        self.start_frame = start_frame
        self.end_frame = end_frame
        self.filepaths = filepaths

    def __repr__(self):
        pass

    def __str__(self):
        pass

    def get_start_frame(self) -> int:
        pass

    def get_end_frame(self) -> int:
        pass

    def get_total_frames(self) -> int:
        pass

    def get_parent_directory(self) -> 'asset.Directory':
        pass


class ExrImageSequence(GenericImageSequence):
    """
    Class for an exr image sequence. Stores related images as a list of filepaths.
    """
    def __init__(self):
        super().__init__()

    def __repr__(self):
        pass

    def __str__(self):
        pass


class JpgImageSequence(GenericImageSequence):
    """
    Class for a jpg image sequence. Stores related images as a list of filepaths.
    """
    def __init__(self):
        super().__init__()

    def __repr__(self):
        pass

    def __str__(self):
        pass


class PngImageSequence(GenericImageSequence):
    """
    Class for a png image sequence. Stores related images as a list of filepaths.
    """
    def __init__(self):
        super().__init__()

    def __repr__(self):
        pass

    def __str__(self):
        pass


def sequences_from_directory(directory: asset.Filepath):
    """
    Returns a list of image sequences from a directory.
    :param directory: Directory to search for image sequences
    :return: List of image sequences
    """
    pass
