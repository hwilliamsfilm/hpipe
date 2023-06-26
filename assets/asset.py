from core.hutils import logger, path
from abc import ABC, abstractmethod
import os

from typing import *
if TYPE_CHECKING:
    pass

log = logger.setup_logger()
log.debug("asset.py loaded")


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
