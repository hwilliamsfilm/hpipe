"""
Module for tanslating different asset file packages to Houdini
"""
import os
from abc import ABCMeta, abstractmethod, ABC
from hpipe.core.hutils import system, logger
from typing import *

try:
    import hou
except ImportError:
    pass

log = logger.setup_logger()
log.debug("Loaded translator.py")


class AbstractAssetAccessor(ABC):
    """
    Abstract class for translating asset file packages to Houdini
    """
    def __init__(self, asset_directory: system.Directory):
        """
        :param asset: assetEntry.AssetEntry
        :param asset_db: data_manager.AssetDataManager
        """
        self.asset_directory = asset_directory

    @abstractmethod
    def get_geometry_file(self) -> List[system.Filepath]:
        """
        Get the geometry file for the asset
        :return: system.Filepath
        """
        pass

    @abstractmethod
    def get_texture_files(self) -> List[system.Filepath]:
        """
        Get the texture files for the asset
        :return: system.Filepath
        """
        pass

    @abstractmethod
    def get_diffuse_albedo(self) -> List[system.Filepath]:
        """
        Get the diffuse map for the asset
        :return: system.Filepath
        """
        pass

    @abstractmethod
    def get_specular_roughness(self) -> List[system.Filepath]:
        """
        Get the specular map for the asset
        :return: system.Filepath
        """
        pass

    @abstractmethod
    def get_normal_map(self) -> List[system.Filepath]:
        """
        Get the normal map for the asset
        :return: system.Filepath
        """
        pass

    @abstractmethod
    def get_displacement_map(self) -> List[system.Filepath]:
        """
        Get the displacement map for the asset
        :return: system.Filepath
        """
        pass


class Megascan3dAssetAccessor(AbstractAssetAccessor):
    """
    Translator for asset packages to Karma USD
    """
    def __init__(self, asset_directory: system.Directory):
        """
        :param asset: assetEntry.AssetEntry
        :param asset_db: data_manager.AssetDataManager
        """
        super().__init__(asset_directory)

    def get_geometry_file(self) -> List[system.Filepath]:
        """
        Get the geometry file for the asset
        :return: system.Filepath
        """
        # Note about LODs
        # The LODs are stored in the same directory as the main asset, asset_LOD#.extension
        extensions = [".fbx", ".obj", ".abc", ".usd"]
        files = []
        for extension in extensions:
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
            files += self.asset_directory.get_files_by_extension(extension, recurse=False)

        # we do not need to deal with LODs for all the textures
        return files

    def get_diffuse_albedo(self) -> List[system.Filepath]:
        """
        Get the diffuse map for the asset
        :return: system.Filepath
        """
        albedo_textures = []
        for texture in self.get_texture_files():
            if "albedo" in texture.basename.lower():
                albedo_textures.append(texture)

        # we need to deal with LODs for the albedo textures
        albedo_textures.sort(key=lambda x: x.basename, reverse=True)
        return albedo_textures

    def get_specular_roughness(self) -> List[system.Filepath]:
        """
        Get the specular map for the asset
        :return: system.Filepath
        """
        spec_textures = []
        for texture in self.get_texture_files():
            if "roughness" in texture.basename.lower():
                spec_textures.append(texture)

        # we need to deal with LODs for the specular textures
        spec_textures.sort(key=lambda x: x.basename, reverse=True)
        return spec_textures

    def get_normal_map(self) -> List[system.Filepath]:
        """
        Get the normal map for the asset
        :return: system.Filepath
        """
        normal_textures = []
        for texture in self.get_texture_files():
            if "normal" in texture.basename.lower():
                normal_textures.append(texture)

        # we need to deal with LODs for the normal textures
        normal_textures.sort(key=lambda x: x.basename, reverse=True)
        return normal_textures

    def get_displacement_map(self, exr=True) -> List[system.Filepath]:
        """
        Get the displacement map for the asset
        :return: system.Filepath
        """
        displacement_textures = []
        for texture in self.get_texture_files():
            if exr:
                if "displacement" in texture.basename.lower() and texture.extension == ".exr":
                    displacement_textures.append(texture)
            else:
                if "displacement" in texture.basename.lower() and texture.extension != ".exr":
                    displacement_textures.append(texture)

        # we need to deal with LODs for the displacement textures
        displacement_textures.sort(key=lambda x: x.basename, reverse=True)
        return displacement_textures

    def get_opacity_map(self) -> List[system.Filepath]:
        """
        Get the opacity map for the asset
        :return: system.Filepath
        """
        opacity_textures = []
        for texture in self.get_texture_files():
            if "opacity" in texture.basename.lower():
                opacity_textures.append(texture)

        # we need to deal with LODs for the opacity textures
        opacity_textures.sort(key=lambda x: x.basename, reverse=True)
        return opacity_textures

    def get_ao_map(self) -> List[system.Filepath]:
        """
        Get the ambient occlusion map for the asset
        :return: system.Filepath
        """
        ao_textures = []
        for texture in self.get_texture_files():
            if "ao" in texture.basename.lower():
                ao_textures.append(texture)

        # we need to deal with LODs for the ao textures
        ao_textures.sort(key=lambda x: x.basename, reverse=True)
        return ao_textures

    def get_translucency_map(self) -> List[system.Filepath]:
        """
        Get the translucency map for the asset
        :return: system.Filepath
        """
        translucency_textures = []
        for texture in self.get_texture_files():
            if "translucency" in texture.basename.lower():
                translucency_textures.append(texture)

        # we need to deal with LODs for the translucency textures
        translucency_textures.sort(key=lambda x: x.basename, reverse=True)
        return translucency_textures

    def get_preview(self) -> List[system.Filepath]:
        """
        Get the preview for the asset
        :return: system.Filepath
        """
        preview = []
        preview_names = ["preview", "thumb", "popup"]
        for texture in self.get_texture_files():
            for name in preview_names:
                if name in texture.basename.lower():
                    preview.append(texture)

        # we need to deal with LODs for the preview textures
        preview.sort(key=lambda x: x.basename, reverse=True)
        return preview


class SpeedTreeAssetAccessor(AbstractAssetAccessor):
    """
    Translator for asset packages to Karma USD
    """
    def __init__(self, asset_directory: system.Directory):
        """
        :param asset: assetEntry.AssetEntry
        :param asset_db: data_manager.AssetDataManager
        """
        super().__init__(asset_directory)

    def get_geometry_file(self) -> List[system.Filepath]:
        """
        Get the geometry file for the asset
        :return: system.Filepath
        """
        # Note about LODs
        # The LODs are stored in the same directory as the main asset, asset_LOD#.extension
        extensions = [".fbx", ".obj", ".abc", ".usd"]
        files = []
        for extension in extensions:
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
            files += self.asset_directory.get_files_by_extension(extension, recurse=False)

        # we do not need to deal with LODs for all the textures
        return files

    def get_diffuse_albedo(self) -> List[system.Filepath]:
        """
        Get the diffuse map for the asset
        :return: system.Filepath
        """
        albedo_textures = []
        for texture in self.get_texture_files():
            if "albedo" in texture.basename.lower():
                albedo_textures.append(texture)

        # we need to deal with LODs for the albedo textures
        albedo_textures.sort(key=lambda x: x.basename, reverse=True)
        return albedo_textures

    def get_specular_roughness(self) -> List[system.Filepath]:
        """
        Get the specular map for the asset
        :return: system.Filepath
        """
        spec_textures = []
        for texture in self.get_texture_files():
            if "roughness" in texture.basename.lower():
                spec_textures.append(texture)

        # we need to deal with LODs for the specular textures
        spec_textures.sort(key=lambda x: x.basename, reverse=True)
        return spec_textures

    def get_normal_map(self) -> List[system.Filepath]:
        """
        Get the normal map for the asset
        :return: system.Filepath
        """
        normal_textures = []
        for texture in self.get_texture_files():
            if "normal" in texture.basename.lower():
                normal_textures.append(texture)

        # we need to deal with LODs for the normal textures
        normal_textures.sort(key=lambda x: x.basename, reverse=True)
        return normal_textures

    def get_displacement_map(self, exr=True) -> List[system.Filepath]:
        """
        Get the displacement map for the asset
        :return: system.Filepath
        """
        displacement_textures = []
        for texture in self.get_texture_files():
            if exr:
                if "displacement" in texture.basename.lower() and texture.extension == ".exr":
                    displacement_textures.append(texture)
            else:
                if "displacement" in texture.basename.lower() and texture.extension != ".exr":
                    displacement_textures.append(texture)

        # we need to deal with LODs for the displacement textures
        displacement_textures.sort(key=lambda x: x.basename, reverse=True)
        return displacement_textures

    def get_opacity_map(self) -> List[system.Filepath]:
        """
        Get the opacity map for the asset
        :return: system.Filepath
        """
        opacity_textures = []
        for texture in self.get_texture_files():
            if "opacity" in texture.basename.lower():
                opacity_textures.append(texture)

        # we need to deal with LODs for the opacity textures
        opacity_textures.sort(key=lambda x: x.basename, reverse=True)
        return opacity_textures

    def get_ao_map(self) -> List[system.Filepath]:
        """
        Get the ambient occlusion map for the asset
        :return: system.Filepath
        """
        ao_textures = []
        for texture in self.get_texture_files():
            if "ao" in texture.basename.lower():
                ao_textures.append(texture)

        # we need to deal with LODs for the ao textures
        ao_textures.sort(key=lambda x: x.basename, reverse=True)
        return ao_textures

    def get_translucency_map(self) -> List[system.Filepath]:
        """
        Get the translucency map for the asset
        :return: system.Filepath
        """
        translucency_textures = []
        for texture in self.get_texture_files():
            if "translucency" in texture.basename.lower():
                translucency_textures.append(texture)

        # we need to deal with LODs for the translucency textures
        translucency_textures.sort(key=lambda x: x.basename, reverse=True)
        return translucency_textures

    def get_preview(self) -> List[system.Filepath]:
        """
        Get the preview for the asset
        :return: system.Filepath
        """
        preview = []
        preview_names = ["preview", "thumb", "popup"]
        for texture in self.get_texture_files():
            for name in preview_names:
                if name in texture.basename.lower():
                    preview.append(texture)

        # we need to deal with LODs for the preview textures
        preview.sort(key=lambda x: x.basename, reverse=True)
        return preview


class KarmaUSDTranslator:
    """
    Translator for asset packages to MTLX USD. Requires the pipe component builder HDA to be loaded.
    """
    def __init__(self, asset_directory: Union['system.Directory', str], component_builder: Optional['hou.node'] = None):
        """
        :param asset_directory: system.Directory for the asset. Will accept a string and convert to system.Directory
        :param component_builder: component_builder hda - if None, will create a new one
        """
        # assuming that the stage is where we are operating.
        # it might not be a good assumption, but I can't think of any use-cases for creating assets outside of the stage
        self.node = hou.node('/stage')

        if isinstance(asset_directory, str):
            asset_directory = system.Directory(asset_directory)

        self.asset_directory = asset_directory
        self.megascan_accessor = Megascan3dAssetAccessor(asset_directory)

        self.component_builder = component_builder
        if component_builder is None:
            self.component_builder = self.create_component_builder()

        self.geometry_subnet: Optional['hou.node'] = hou.node(f"{self.component_builder.path()}/input/sopnet/geo/")
        self.do_shader = hou.node(f"{self.geometry_subnet.path()}/do_shader")
        self.file_sop: Optional['hou.node'] = hou.node(f"{self.geometry_subnet.path()}/input_file")
        self.material_library = hou.node(f"{self.component_builder.path()}/material_library")
        self.material_assign = hou.node(f"{self.component_builder.path()}/material_assign")
        self.mtlx_template = hou.node(f"{self.material_library.path()}/mtlx_template")
        self.collection_template = hou.node(f"{self.material_library.path()}/mtlx_collection")
        self.component_output = hou.node(f"{self.component_builder.path()}/output")

        self.import_geometry()
        self.asset_shader, self.collection_shader = self.create_mtlx_shader()
        self.set_shader_paths()
        self.assign_material()
        self.set_asset_name()

    def create_component_builder(self) -> 'hou.node':
        """
        Create a pipe component builder wrapper hda to build the asset out.
        :return: system.Filepath
        """
        component_builder = self.node.createNode('pipe_component_builder')
        self.component_builder = component_builder
        return self.component_builder

    def import_geometry(self) -> bool:
        """
        This function:
        - sets the filepath for the file node

        :return: system.Filepath
        """
        try:
            self.file_sop.parm('file').set(self.megascan_accessor.get_geometry_file()[-1].system_path())
        except Exception as e:
            log.debug(f"Could not find geometry file for {self.asset_directory}")
            self.do_shader.parm('input').set(0)

        return True

    def create_mtlx_shader(self, material_name: Optional[str] = None) -> 'hou.node':
        """
        Create materialx shader from the megascan directory
        :return: hou.node of the materialx shader
        """

        log.debug(f"Creating MaterialX shader from {self.asset_directory}")
        if not material_name:
            material_name = self.asset_directory.get_basename()

        copied_nodes = self.material_library.copyItems([self.mtlx_template, self.collection_template])
        mtlx_template = copied_nodes[0]
        collection_template = copied_nodes[1]

        mtlx_template.setName(f"{material_name}_mtlx", unique_name=True)
        collection_template.setName(f"collection_{material_name}", unique_name=True)

        return [mtlx_template, collection_template]

    def set_shader_paths(self) -> bool:
        """
        Set the shader paths for the materialx shader
        :return: True if successful
        """
        albedo_node = hou.node(f"{self.asset_shader.path()}/albedo")
        roughness_node = hou.node(f"{self.asset_shader.path()}/roughness")
        normal_node = hou.node(f"{self.asset_shader.path()}/normal")
        displacement_node = hou.node(f"{self.asset_shader.path()}/displacement")

        albedo_node.parm('file').set(self.megascan_accessor.get_diffuse_albedo()[-1].system_path())
        roughness_node.parm('file').set(self.megascan_accessor.get_specular_roughness()[-1].system_path())
        normal_node.parm('file').set(self.megascan_accessor.get_normal_map()[-1].system_path())
        displacement_node.parm('file').set(self.megascan_accessor.get_displacement_map(exr=True)[-1].system_path())
        return True

    def assign_material(self) -> bool:
        """
        Assign the material to the geometry
        :return: True if successful
        """
        # TODO: need to figure out how to assign the material if multiple materials are created
        self.material_assign.parm('matspecpath1').set(f"/ASSET/mtl/{self.collection_shader.name()}")
        return True

    def set_asset_name(self):
        """
        Create variants from the asset
        :return: system.Filepath
        """
        self.component_output.setName(f"MS_{self.asset_directory.get_basename()}", unique_name=True)

    def configure_asset(self):
        """
        Configures the asset dictated by the directory.
        """
        pass
