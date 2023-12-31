"""

USD LAYER STRUCTURE

- Each layer has its own hip file

shot.usd
    sublayer[
        - LAYOUT.usda
        - ANIM.usa
        - FX.usda
        - RENDER.usda
        ]
"""
import os
from core.hutils import system, logger
from core import data_manager, constants
from pxr import Usd, UsdGeom, Sdf

log = logger.setup_logger()
log.debug("husd_util.py loaded")


class ShotUsd:
    """
    Shot USD class for managing the shot USD file.
    """
    def __init__(self, project_name: str, shot_name: str):
        self.database = data_manager.ProjectDataManager()
        self.project = self.database.get_project(project_name)
        self.shot = self.project.get_shot(shot_name)
        self.usd_filepath = self.get_usd_file()

    def get_usd_file(self) -> 'system.Filepath':
        """
        Returns the USD file path
        :return:
        """
        usd_path = self.shot.get_usd_path()
        usd_exists = os.path.exists(usd_path.system_path())
        self.usd_filepath = usd_path

        if not usd_exists:
            log.warning("USD file does not exist. Creating new one.")
            self.create_shot_usd_file(usd_path)
            for layer in constants.SHOT_USD_LAYERS:
                usd_output_path = self.shot.get_usd_directory()
                layer_path = f"{usd_output_path.system_path()}/{layer}/{layer}.usda"
                log.debug(f"Layer path: {layer_path}")
                layer_filepath = system.Filepath(layer_path)
                self.create_shot_usd_file(layer_filepath)
                self.add_layer(layer_filepath)

        return usd_path

    def create_shot_usd_file(self, filepath: 'system.Filepath') -> 'system.Filepath':
        """
        Creates a new USD file.
        :return: filepath of the newly created USD file
        """
        log.debug(f"Creating new USD file: {filepath.system_path()}")
        stage = Usd.Stage.CreateNew(filepath.system_path())
        stage.Save()

        return filepath

    def add_layer(self, new_layer: 'system.Filepath') -> bool:
        """
        Adds a layer to the USD file.
        :param new_layer:
        :param layer_name:
        :return:
        """
        if not os.path.exists(new_layer.system_path()):
            log.warning("USD file does not exist. Cannot add layer.")
            return False
        stage = Usd.Stage.Open(self.usd_filepath.system_path())

        layer_relative_path = self.absolute_to_relative(new_layer.system_path())
        log.debug(f"Layer relative path: {layer_relative_path}")
        root_layer = stage.GetRootLayer()
        root_layer.subLayerPaths.append(layer_relative_path)
        log.debug(f"Root layer: {root_layer.ExportToString()}")
        usda = stage.GetRootLayer().ExportToString()
        log.debug(usda)
        stage.Save()
        return True

    def remove_layer(self, layer_name: str) -> bool:
        """
        Removes a layer from the USD file.
        :param layer_name:
        :return:
        """
        raise NotImplementedError

    def get_layers(self) -> list:
        """
        Returns the layers of the USD file.
        :return:
        """
        raise NotImplementedError

    @staticmethod
    def create_usd_hierarchy(usd_stage: 'Usd.Stage', recursion_hierarchy: dict, parent=None) -> None:
        """
        Creates a USD hierarchy based on the hierarchy dict.
        :param usd_stage:
        :param recursion_hierarchy:
        :return:
        """
        for key, value in recursion_hierarchy.items():

            # check if value is a dictionary
            if value:
                # create prim at the key
                UsdGeom.Xform.Define(usd_stage, f'/{key}')

                # create new parent path for the next iteration
                if not parent:
                    new_parent = f"/{key}"
                else:
                    new_parent = f"/{parent}/{key}"

                # recurse
                ShotUsd.create_usd_hierarchy(usd_stage, value, new_parent)
            else:

                # create prim at the key
                if not parent:
                    UsdGeom.Xform.Define(usd_stage, f'/{key}')
                else:
                    UsdGeom.Xform.Define(usd_stage, f'{parent}/{key}')

    def absolute_to_relative(self, absolute_path: str) -> str:
        """
        Converts an absolute path to relitive to the shot.usd file.
        :param absolute_path:
        :return:
        """
        import os
        shot_path = self.get_usd_file().get_parent_directory().system_path()
        layer_path = system.Filepath(absolute_path).system_path()
        log.debug(f"Shot path: {shot_path}")
        log.debug(f"Layer path: {layer_path}")
        relative_path = os.path.relpath(layer_path, shot_path)
        return relative_path

