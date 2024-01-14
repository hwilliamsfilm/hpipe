"""

"""
import os
from abc import ABCMeta, abstractmethod, ABC
from dcc.houdinipipe.assetTranslator import asset_accessor
from core.hutils import system, logger
from typing import *
import re

try:
    import hou
except ImportError:
    pass

log = logger.setup_logger()
log.debug("Loaded asset_accessor.py")


class AssetBuilder:
    """
    Translator for asset packages to MTLX USD. Requires the pipe component builder HDA to be loaded.
    """
    def __init__(self, generic_accessor: asset_accessor.AbstractAssetAccessor):
        """
        :param asset_directory: system.Directory for the asset. Will accept a string and convert to system.Directory
        :param component_builder: component_builder hda - if None, will create a new one
        """
        # assuming that the stage is where we are operating.
        # it might not be a good assumption, but I can't think of any use-cases for creating assets outside of the stage
        self.node = hou.node('/stage')
        self.accessor = generic_accessor
        self.blueprint = self.accessor.get_blueprint()
        self.component_geometry_list = []

    def create_component_geometry(self):
        """
        Create the component geometry and any variants (if applicable)
        """
