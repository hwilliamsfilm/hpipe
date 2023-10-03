"""
USD Asset Class
"""

from typing import *
from pxr import Usd, UsdGeom
from assets import asset
from core.hutils import logger, system

log = logger.setup_logger()
log.debug("usdAsset.py loaded")


class UsdAsset(asset.Asset):
    """
    Class for a USD asset. Stores the all elements of a USD asset to be used in the pipeline.
    """
    def __init__(self, filepath: Optional['system.Filepath'] = None, asset_name: str = ''):
        super().__init__(asset_name)
        if not filepath:
            self.filepath = self.generate_asset_filepath()
        self.asset_type = asset.AssetType.USD

    def __repr__(self) -> str:
        return f"ProjectFile <{self.filepath}> from " \
               f"<{self.filepath.get_parent_directory()}>"

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
