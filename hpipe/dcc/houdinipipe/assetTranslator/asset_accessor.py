"""
Module that focuses on getting the files from an asset package directory with custom implementations for each asset
package type.

Main function for each accessor class is the get_material_textures() function which returns a dictionary of the materials

asset_name = {

    # If the asset has variants, the variant name is the key, otherwise the key is 'default'
    "variant_name": {

        # The geometry file for the asset
        "geo": system.Filepath(""),

        # The selection string for the geometry that will separate it from other geometry (e.g. with a blast node)
        "selection": str,

        # The pbr shaders for the asset
        "materials": {,

            # The material properties for the asset
            "material_name": {
                "selection": str,
                "albedo": system.Filepath(""),
                "roughness": system.Filepath(""),
                "normal": system.Filepath(""),
                "displacement": system.Filepath(""),
            },
        },
    },
}
"""


from abc import ABCMeta, abstractmethod, ABC
from hpipe.core.hutils import system, logger
from typing import *
import re
import natsort

try:
    import hou
except ImportError:
    pass

log = logger.setup_logger()
log.debug("Loaded asset_accessor.py")


class AbstractAssetAccessor(ABC):
    """
    Abstract class for translating asset file packages to Houdini
    """
    def __init__(self, asset_directory: system.Directory):
        """
        :param asset_directory: assetEntry.AssetEntry
        """
        self.asset_directory = asset_directory

    @abstractmethod
    def get_blueprint(self) -> Dict[str, Dict[str, Union[system.Filepath, str]]]:
        """
        Get a dictionary of the materials for the object with all relevant materials.
        """
        pass


class Megascan3dAssetAccessor(AbstractAssetAccessor):
    """
    Translator for asset packages to Karma USD
    """
    def __init__(self, asset_directory: Union[system.Directory, str]):
        """
        :param asset: assetEntry.AssetEntry
        :param asset_db: data_manager.AssetDataManager
        """
        if isinstance(asset_directory, str):
            asset_directory = system.Directory(asset_directory)

        super().__init__(asset_directory)

        self.asset_directory = asset_directory
        self.has_geo_variants = False

    def get_variants(self) -> Optional[List[system.Directory]]:
        """
        Get variant names for the asset
        """
        subdirectories = self.asset_directory.get_subdirectories()
        variant_directories = []
        for subdirectory in subdirectories:
            if "var" in subdirectory.system_path().lower():
                variant_directories.append(subdirectory)
                self.has_geo_variants = True

        log.debug(f"Variant directories: {variant_directories}")
        if len(variant_directories) == 0:
            return None

        return variant_directories

    def get_variant(self, variant_name: str) -> Optional[system.Directory]:
        """
        Get the variant directory for the specified variant name
        """
        variants = self.get_variants()
        if not variants:
            return None

        for variant in variants:
            if variant_name in variant.system_path():
                return variant

        return None

    def has_variants(self) -> bool:
        """
        Check if the asset has variants
        """
        variants = self.get_variants()
        if not variants:
            return False
        return True

    def get_geometry_files(self, subdirectory: Optional[system.Directory] = None) -> List[system.Filepath]:
        """
        Get the geometry file for the asset
        :return: system.Filepath
        """
        # Note about LODs
        # The LODs are stored in the same directory as the main asset, asset_LOD#.extension
        extensions = [".fbx", ".obj", ".abc", ".usd"]
        files = []
        for extension in extensions:
            if subdirectory:
                files += subdirectory.get_files_by_extension(extension)
            else:
                files += self.asset_directory.get_files_by_extension(extension)

        # should order the list reverse LOD order lambda the file name. The last index should be the highest LOD
        files.sort(key=lambda x: x.basename, reverse=True)

        return files

    def get_texture_files(self) -> List[system.Filepath]:
        """
        Get the texture files for the asset
        :return: system.Filepath
        """
        # Note about LODs
        # The LODs are stored in the same directory as the main asset, asset_LOD#.extension
        extensions = [".tga", ".png", ".jpg", ".jpeg", ".exr", ".tif", ".tiff"]
        files = []
        for extension in extensions:
            files += self.asset_directory.get_files_by_extension(extension, recurse=True)

        return files

    def get_texture(self, texture_name) -> List[system.Filepath]:
        """
        Get the specified texture from the megascan asset directory. First, we have to identify which textures qualify,
        then we need to find the highest resolution textures, and finally we need to sort the textures by name to get the
        highest LOD.
        :param texture_name: The name of the texture to get
        :return: List[system.Filepath] of the textures (last being the highest LOD)
        """

        # This code snippet only works with a few qualifiers that for now we should check for and raise an error if
        # they are not present.

        albedo_textures = []
        highest_resolution = 0
        for texture in self.get_texture_files():

            # Billboard textures are the textures that are used for a 2d card. We don't need these.
            if "billboard" in texture.basename.lower():
                continue

            if texture_name in texture.basename.lower():
                albedo_textures.append(texture)
                match = re.search(r'(\d+K)', texture.system_path())
                resolution = int(match.group()[:-1])

                if resolution > highest_resolution:
                    highest_resolution = resolution

        highest_resolution_textures = []
        for texture in albedo_textures:
            if f"_{highest_resolution}K" in texture.system_path():
                highest_resolution_textures.append(texture)

        highest_resolution_textures.sort(key=lambda x: x.basename, reverse=True)

        return highest_resolution_textures

    def get_blueprint(self) -> Dict[str, Dict[str, Union[system.Filepath, str]]]:
        """
        Get a dictionary of the materials for the object with all relevant materials.
        """
        material_textures = {}
        geometry_selection = "*"
        material_selection = "*"
        if not self.has_variants():
            geometry_files = self.get_geometry_files()
            material_textures['default'] = {
                'geo': geometry_files[-1] if len(geometry_files) > 0 else None,
                'variant_selection': geometry_selection,
                'pbr_shader': {
                    'material_selection': material_selection,
                    'albedo': self.get_texture('albedo')[-1],
                    'roughness': self.get_texture('roughness')[-1],
                    'normal': self.get_texture('normal')[-1],
                    'displacement': self.get_texture('displacement')[-1],
                },
            }
        else:
            variants = self.get_variants()
            variants_sorted = natsort.natsorted(variants, key=lambda x: x.get_basename())
            log.debug(f"Variants sorted: {variants_sorted}")
            for variant in variants_sorted:
                geometry_files = self.get_geometry_files(subdirectory=variant)
                material_textures[variant.get_basename()] = {
                    'geo': geometry_files[-1] if len(geometry_files) > 0 else None,
                    'variant_selection': geometry_selection,
                    'pbr_shader': {
                        'material_selection': material_selection,
                        'albedo': self.get_texture('albedo')[-1],
                        'roughness': self.get_texture('roughness')[-1],
                        'normal': self.get_texture('normal')[-1],
                        'displacement': self.get_texture('displacement')[-1],
                    },
                }

        return material_textures

