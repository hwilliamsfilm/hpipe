"""
Module containing the helper functions for the component output node.
"""

from dcc.houdinipipe import session
from core import data_manager
from core.hutils import logger, system
from assets import usdAsset

from typing import *

log = logger.setup_logger()
log.debug("component_output.py loaded")


class UsdAssetBuilder:
    """
    Class for building usd asset from component output node.
    """
    def __init__(self, node: 'hou.Node'):
        self.node = node
        log.debug(f"Node {node.name()} is {node.type().name()}.")
        if node.type().name() != 'componentoutput':
            if node.type().name() == 'usd_rop':
                self.node = node.parent()
                log.debug(f"Node {self.node.name()} is {self.node.type().name()}.")
            else:
                log.debug(f"Node {node.name()} is {node.type().name()}.")
                raise TypeError("Node is not a component output node.")

        self.database = data_manager.ProjectDataManager()
        self.config = data_manager.ConfigDataManager()
        self.node_name = self.node.name()

    def get_filename(self) -> str:
        """
        Gets the filename of the node.
        :return: Filename of the node.
        """
        return self.node_name + '.usd'

    def get_output_path(self) -> str:
        """
        Gets the output path of the node.
        :return: Output path of the node.
        """
        asset_path = self.config.get_config('ASSETS_ROOT')
        node_name = self.node_name
        output_path = system.Filepath(f"{asset_path}/{node_name}/{self.get_filename()}")
        return output_path.system_path()

    def get_root_prim(self) -> str:
        """
        Gets the root prim of the node.
        :return: Root prim of the node.
        """
        root_prim = f'/{self.node_name}'
        return root_prim

    def register_usd_asset(self) -> bool:
        """
        Registers the usd asset to the database.
        :return: True if successful.
        """
        filepath= self.get_output_path()
        asset_name = self.node_name
        return usdAsset.UsdAssetManager(usd_filepath=filepath, asset_name=asset_name).add_asset_entry()


