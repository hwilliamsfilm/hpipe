"""
USD Asset Class
"""

from typing import *
from pxr import Usd, UsdGeom
from assets import asset
from core.hutils import logger, system
from core import assetEntry, data_manager
import os, sys

log = logger.setup_logger()
log.debug("usdAsset.py loaded")


class UsdAsset(asset.Asset):
    """
    Class for a USD asset. Stores the all elements of a USD asset to be used in the pipeline.
    """
    def __init__(self, filepath: Optional['system.Filepath'] = None, asset_name: str = ''):
        super().__init__(asset_name=asset_name)
        self.filepath = filepath
        if not self.filepath:
            self.filepath = self.generate_asset_filepath()
        self.asset_type = asset.AssetType.USD

    def __repr__(self) -> str:
        return f"ProjectFile <{self.filepath}> from " \
               f"<{self.filepath.get_parent_directory()}>"

    def get_thumbnail(self) -> 'system.Filepath':
        """
        Gets the thumbnail of the asset.
        :return: Thumbnail of the asset.
        """
        pass

    def get_filepath(self) -> 'system.Filepath':
        """
        Gets the filepath of the asset.
        :return: Filepath of the asset.
        """
        return self.filepath

    def generate_asset_filepath(self) -> 'system.Filepath':
        """
        Generates a filepath for the asset.
        :return: Filepath for the asset.
        """
        pass

    def to_dict(self) -> Dict[str, Any]:
        """
        Converts the asset to a dictionary.
        :return: Dictionary representation of the asset.
        """
        return {
            'asset_name': self.asset_name,
            'filepath': self.filepath.system_path()
        }

    @classmethod
    def from_dict(cls, asset_dict: Dict[Any, Any]) -> Union[None, Any]:
        """
        Converts a dictionary to an asset.
        :param asset_dict: Dictionary to convert.
        :return: None
        """
        asset_name = asset_dict['asset_name']
        filepath = system.Filepath(asset_dict['filepath'])
        return cls(filepath=filepath, asset_name=asset_name)


class UsdAssetManager:
    """
    Class for managing USD assets and registering into the asset database.
    """
    def __init__(self, usd_filepath: str = '', asset_name: str = ''):
        self.config = data_manager.ConfigDataManager()
        self.asset_manager = data_manager.AssetDataManager()
        self.usd_filepath = usd_filepath
        self.asset_name = asset_name
        if not asset_name:
            self.asset_name = os.path.basename(self.usd_filepath).split('.')[0].lower()
        self.validate_path()
        self.check_duplicate()
        self.asset_instance = self.create_asset_instance()
        self.asset_entry = self.create_asset_entry()

    def validate_path(self) -> bool:
        """
        Validates the path of the USD file.
        :return: Whether the path is valid or not.
        """
        assets_root = self.config.get_config('ASSETS_ROOT')
        if assets_root not in self.usd_filepath:
            log.warning(f"USD file is not in the assets root: {self.usd_filepath}")
            return False
        return True

    def validate_thumbnail(self) -> bool:
        """
        Validates the thumbnail of the USD file.
        :return: Whether the thumbnail is valid or not.
        """
        filepath = system.Filepath(self.usd_filepath)
        thumbnail = filepath.get_parent_directory().directory_path() + '/thumbnail.png'
        if not system.Filepath(thumbnail).exists():
            log.warning(f"Thumbnail does not exist: {thumbnail}")
            return False
        return True

    def check_duplicate(self) -> bool:
        """
        Checks if the USD file is a duplicate.
        :return: Whether the USD file is a duplicate or not.
        """
        asset_list = self.asset_manager.get_assets()
        for item in asset_list:
            if item.asset_instance.asset_name == self.asset_name:
                log.warning(f"USD file already exists: {self.usd_filepath}")
                return False
        return True

    def create_asset_instance(self) -> 'asset.Asset':
        """
        Creates an asset instance for the USD file.
        :return: Asset instance for the USD file.
        """
        return UsdAsset(filepath=system.Filepath(self.usd_filepath),
                        asset_name=self.asset_name)

    def create_asset_entry(self) -> 'assetEntry.AssetEntry':
        """
        Creates an asset entry for the USD file.
        :return: Asset entry for the USD file.
        """
        return assetEntry.AssetEntry(asset_instance=self.asset_instance)

    def add_asset_entry(self) -> bool:
        """
        Adds the asset entry to the database.
        :return: Whether the asset entry was added or not.
        """
        return self.asset_manager.add_asset(self.asset_entry)


