from core.hutils import logger, path
from abc import ABC, abstractmethod
import os

from typing import *
if TYPE_CHECKING:
    pass

log = logger.setup_logger()
log.debug("asset.py loaded")


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
