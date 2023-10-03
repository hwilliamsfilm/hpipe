"""
Asset database entry class. This is abstracted from asset.Asset because it is meant to be used in the database, whereas
asset.Asset is meant to be used on the fly in the pipe.
"""

from assets import asset
from typing import *


class AssetEntryDict(TypedDict):
    asset_name: str
    asset_type: str
    asset_filepath: str
    description: str


class AssetEntry:
    """
    Class for an asset entry in the database. This is meant to be used to store information about an asset in the
    database, and is not meant to be used on the fly.
    """
    def __init__(self, asset_instance: 'asset.Asset', description: str = ''):
        self.asset_name = asset_instance.asset_name
        self.asset_type = asset_instance.asset_type
        self.asset_filepath = asset_instance.get_filepath()
        self.description = description

    @classmethod
    def from_dict(cls, asset_entry_dict: 'AssetEntryDict') -> 'AssetEntry':
        """
        Creates an AssetEntry object from a dictionary.
        :param asset_entry: Dictionary of the asset entry.
        :return: AssetEntry object.
        """

        asset_name = asset_entry_dict['asset_name']
        asset_type = asset_entry_dict['asset_type']
        asset_filepath = asset_entry_dict['asset_filepath']
        description = asset_entry_dict['description']

        shot = cls(asset_name=asset_name, asset_type=asset_type, asset_filepath=asset_filepath,)
        return shot

    def to_dict(self) -> dict:
        """
        Converts the AssetEntry to a dictionary.
        :return: Dictionary of the AssetEntry.
        """
        return {
            'asset_name': self.asset_name,
            'asset_type': self.asset_type,
            'asset_filepath': self.asset_filepath,
            'description': self.description
        }

