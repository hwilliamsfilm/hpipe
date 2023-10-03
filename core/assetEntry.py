"""
Asset database entry class. This is abstracted from asset.Asset because it is meant to be used in the database, whereas
asset.Asset is meant to be used on the fly in the pipe.
"""

from assets import asset, usdAsset
from typing import *
from core.hutils import system, logger
from core import data_manager
from assets import reviewable

log = logger.setup_logger()
log.debug("assetEntry.py loaded")


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
    def __init__(self, asset_instance: 'asset.Asset', asset_date: str=''):
        self.asset_instance = asset_instance
        self.asset_date = asset_date
        if asset_date == '':
            self.asset_date = system.SystemConfig().get_system_date()

    @classmethod
    def from_dict(cls, asset_entry_dict: 'AssetEntryDict') -> 'AssetEntry':
        """
        Creates an AssetEntry object from a dictionary.
        :param asset_entry: Dictionary of the asset entry.
        :return: AssetEntry object.
        """

        asset_date = asset_entry_dict['date']
        asset_instance = asset_factory(asset_entry_dict)

        shot = cls(asset_instance=asset_instance,
                   asset_date=asset_date)

        return shot

    def to_dict(self) -> dict:
        """
        Converts the AssetEntry to a dictionary.
        :return: Dictionary of the AssetEntry.
        """
        asset_dict = self.asset_instance.to_dict()
        asset_dict['date'] = self.asset_date
        asset_dict['asset_name'] = self.asset_instance.asset_name
        asset_dict['asset_type'] = self.asset_instance.asset_type.name

        return asset_dict


def asset_factory(asset_dict: Union[Any, Any]) -> 'asset.Asset':
    """
    Factory for creating an asset from a dictionary. Contains the
    implementation detials for each asset type.
    :returns: Asset object.
    """
    asset_type = asset_dict['asset_type']
    if asset_type == 'USD':
        return usdAsset.UsdAsset.from_dict(asset_dict)
    else:
        raise TypeError(f"Asset type {asset_type} not supported.")


def reviewable_factory(asset_list: List['AssetEntry']) -> List['reviewable.Reviewable']:
    """
    Factory for creating a reviewable from asset entries. Contains the
    implementation details for each asset type. Added to create reviewables for the pipeDisplay app.
    :param asset_list: List of dictionaries of reviewables.
    :return: List of reviewables.
    """
    reviewables = []
    for asset_entry in asset_list:
        asset_instance = asset_entry.asset_instance
        if asset_instance.asset_type == asset.AssetType.USD:
            reviewable_directory = asset_instance.get_filepath().get_parent_directory()
            log.debug(f"Reviewable directory: {reviewable_directory}")
            reviewables.append(reviewable.UsdReviewable(reviewable_name=asset_instance.asset_name,
                                                        reviewable_directory=reviewable_directory,
                                                        usd_asset=asset_instance))
        else:
            log.debug(f"Asset type {asset_instance.asset_type} not supported.")

    return reviewables
