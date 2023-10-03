from abc import ABC, abstractmethod
from typing import *

from core.hutils import logger
from core.hutils import system
from enum import Enum

if TYPE_CHECKING:
    pass

log = logger.setup_logger()
log.debug("asset.py loaded")


class AssetType(Enum):
    """
    Enum for the different types of assets.
    """
    USD = 0
    IMAGE_SEQUENCE = 1
    PROJECT_FILE = 2
    GENERIC = 3
    OTHER = 4


class Asset(ABC):
    """
    Base class for an asset on disk. This class is meant to be very generic and only describe the most basic
    properties of an asset. It is meant to be subclassed to create more specific asset types, like images,
    project files, etc.
    """

    @abstractmethod
    def __init__(self, asset_name: str):
        self.asset_name = asset_name
        self.asset_type = AssetType.GENERIC
        pass
