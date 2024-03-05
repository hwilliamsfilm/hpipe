from abc import ABC, abstractmethod
from typing import *

from hpipe.core.hutils import logger
from hpipe.core.hutils import system
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

    @abstractmethod
    def get_filepath(self) -> Union['system.Filepath', 'system.Directory']:
        """
        Gets the filepath of the asset.
        :return: Filepath of the asset.
        """
        pass

    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """
        Converts the asset to a dictionary.
        :return: Dictionary representation of the asset.
        """
        pass

    @abstractmethod
    def from_dict(self, asset_dict: Dict[Any, Any]) -> Union[None, Any]:
        """
        Converts a dictionary to an asset.
        :param asset_dict: Dictionary to convert.
        :return: None
        """
        pass


class NullAsset(Asset):
    """
    Null asset class. This class is meant to be used as a placeholder for when an asset is not found.
    """
    def __init__(self, asset_name: str = 'NULL'):
        super().__init__('NULL')
        self.asset_type = AssetType.OTHER

    def get_filepath(self) -> Union['system.Filepath', 'system.Directory']:
        """
        Gets the filepath of the asset.
        :return: Filepath of the asset.
        """
        return system.Directory(r'Y:/_global_assets/assets')

    def to_dict(self) -> Dict[str, Any]:
        """
        Converts the asset to a dictionary.
        :return: Dictionary representation of the asset.
        """
        return {
            'asset_name': 'NULL',
            'asset_type': 'OTHER',
            'asset_filepath': 'NULL',
            'description': 'NULL'
        }

    def from_dict(self, asset_dict: Dict[Any, Any]) -> Union[None, Any]:
        """
        Converts a dictionary to an asset.
        :param asset_dict: Dictionary to convert.
        :return: None
        """
        return NullAsset()
