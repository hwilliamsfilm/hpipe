"""
Asset database entry class. This is abstracted from asset.Asset because it is meant to be used in the database, whereas
asset.Asset is meant to be used on the fly in the pipe.
"""

from assets import asset


class AssetEntry:
    """
    Class for an asset entry in the database. This is meant to be used to store information about an asset in the
    database, and is not meant to be used on the fly.
    """
    def __init__(self, asset_instance: 'asset.Asset', description: str = ''):
        self.asset_name = asset_instance.asset_name
        self.asset_type = asset_instance.asset_type
        self.asset_filepath = asset_instance