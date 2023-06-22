import os.path

from core.hutils import logger, path
from abc import ABC, abstractmethod
import os

from typing import *
if TYPE_CHECKING:
    pass

log = logger.setup_logger()
log.debug("asset.py loaded")


class Filepath:
    """
    Base class for a filepath. This class is meant to be very generic and only describe the most basic
    properties of a filepath. It is meant to be subclassed to create more specific filepath types, like images,
    project files, etc.
    """

    def __init__(self, filepath_path: str, filepath_name: str = ''):
        self.filepath_path = path.fix_path(filepath_path)
        if filepath_name == '':
            filepath_name = os.path.basename(filepath_path)
        self.filepath_name = filepath_name
        self.basename = os.path.basename(filepath_path)
        self.extension = os.path.splitext(filepath_path)[1]

    def has_frame_number(self) -> bool:
        """
        Checks if the filepath has a frame number.
        :return: True if the filepath has a frame number, False if not
        """
        has_number_in_name = any(char.isdigit() for char in self.basename)

        if not has_number_in_name:
            return False

        if '_' not in self.basename:
            return False

        return True


    def get_frame_number(self) -> int:
        """
        Gets the frame number from the filepath.
        :return: frame number
        """
        if not self.has_frame_number():
            return -1

        return 1


class Directory:
    """
    Base class for a directory on disk. This class is meant to be very generic and only describe the most basic
    properties of a directory. It is meant to be subclassed to create more specific directory types.
    """
    def __init__(self, directory_path: str, directory_name: str = ''):
        self.directory_path = path.fix_path(directory_path)
        if directory_name == '':
            directory_name = os.path.basename(directory_path)
        self.directory_name = directory_name


class Asset(ABC):
    """
    Base class for an asset on disk. This class is meant to be very generic and only describe the most basic
    properties of an asset. It is meant to be subclassed to create more specific asset types, like images,
    project files, etc.
    """

    @abstractmethod
    def __init__(self, asset_name: str):
        self.asset_name = asset_name
        pass
