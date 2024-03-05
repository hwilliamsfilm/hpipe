"""
Module that defines what a reviewable is. Reviewables in the pipe are directories of (potentially many) image sequences
that are usually the same element with different specifications. For example, a reviewable could be a comp, which might
have a png sequence, exr sequence, and an MOV file.

A reviewable must have a folder/subfolder structure.

Reviewable Directory [COMP]
    - thumbnail.jpg (optional)
    - compressed mp4 (optional)
    - EXR
        - ###.exr
    - PNG
        - ###.png
    - MOV
    - etc.
Reviewable Directory [RENDER]
    - thumbnail (optional)
    - compressed mp4 (optional)
    - beauty
        - ###.exr
    - deep
        - deep_###.exr
    - etc.
Reviable Directory [Asset]
    - thumbnail.jpg (optional)
    - USD
    - Texture

"""
from typing import *
from typing import List

from abc import ABC, abstractmethod

from hpipe.assets.asset import Asset

try:
    import oiio
    from oiio import ImageBuf, ImageSpec, ImageOutput
except ImportError:
    pass

from hpipe.assets import asset, imageSequence
from hpipe.core.hutils import logger, system
import os

if TYPE_CHECKING:
    pass

log = logger.setup_logger()
log.debug("reviewable.py loaded")


class Reviewable(asset.Asset):
    """
    Generic class for a reviewable. Stores the all elements of a reviewable.
    """
    def __init__(self, reviewable_name: str, reviewable_directory: 'system.Directory'):
        super().__init__(reviewable_name)
        self.reviewable_directory = reviewable_directory
        self.asset_type = asset.AssetType.IMAGE_SEQUENCE

    @abstractmethod
    def get_filepath(self) -> Union['system.Filepath', 'system.Directory']:
        """
        Gets the filepath of the asset.
        :return: Filepath of the asset.
        """
        pass

    @classmethod
    def from_dict(cls, asset_dict: Dict[Any, Any]) -> Union[None, Any]:
        """
        Converts a dictionary to an asset.
        :param asset_dict: Dictionary to convert.
        :return: None
        """
        reviewable_directory = system.Filepath(asset_dict['reviewable_directory'])
        reviewable_name = asset_dict['reviewable_name']
        return cls(reviewable_name, reviewable_directory)

    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_thumbnail_image(self) -> Optional[system.Filepath]:
        """
        Recursively search a directory for images
        :return: Path to the first image found in the reviewable.
        """
        pass

    @abstractmethod
    def generate_thumbnail(self, thumbnail_path: 'system.Filepath') -> system.Filepath:
        """
        Generates a thumbnail for the reviewable.
        :param thumbnail_path: Path to save the thumbnail to.
        :return: True if the thumbnail was generated successfully, False otherwise.
        """
        pass


class SequenceReviewable(Reviewable):
    """
    Class for a reviewable. Stores the all elements of a reviewable.
    """
    def __init__(self, reviewable_name: str, reviewable_directory: 'system.Directory'):
        super().__init__(reviewable_name, reviewable_directory)
        self.reviewable_directory = reviewable_directory
        self.asset_type = asset.AssetType.IMAGE_SEQUENCE

    def __repr__(self) -> str:
        return f"Reviewable <{self.asset_name}> from " \
               f"<{self.reviewable_directory}>"

    def get_filepath(self) -> 'system.Filepath':
        """
        Gets the filepath of the asset.
        :return: Filepath of the asset.
        """
        return self.reviewable_directory

    @classmethod
    def from_dict(cls, asset_dict: Dict[Any, Any]) -> Union[None, Any]:
        """
        Converts a dictionary to an asset.
        :param asset_dict: Dictionary to convert.
        :return: None
        """
        # reviewable_directory = system.Filepath(asset_dict['reviewable_directory'])
        # reviewable_name = asset_dict['reviewable_name']
        # return cls(reviewable_name, reviewable_directory)
        # temporarily disabled - i dont think this is needed because we aren't saving reviewables to the database
        pass

    def to_dict(self) -> Dict[str, Any]:
        pass

    def is_valid(self) -> bool:
        """
        Checks if the reviewable is valid. A reviewable is valid if it has at least one element and is in a valid
        pipe directory.
        # TODO: I'm not sure its clear what a reviewable really is.
        :return: True if the reviewable is valid, False otherwise.
        """
        # In order to check if the reviewable is valid, we need to check if it has at least one element.
        # But in order to check if it has at least one element, we need to know what the elements are.
        # Would be too slow to check every element, might need to move to a database for caching.
        return True

    def get_reviewable_image_sequences(self) -> List['imageSequence.GenericImageSequence']:
        """
        Returns all image sequences in the reviewable.
        :return: List of image sequences in the reviewable.
        """
        reviewable_image_sequences = []
        for directory in self.get_subdirectories():
            if 'temp' in directory.directory_path or 'tmp' in directory.directory_path:
                continue
            for image_sequence in imageSequence.sequences_from_directory(directory, temp=False):
                reviewable_image_sequences.append(image_sequence)
        return reviewable_image_sequences + imageSequence.sequences_from_directory(self.reviewable_directory)

    def get_thumbnail_image(self) -> Optional[system.Filepath]:
        """
        Recursively search a directory for images
        :return: Path to the first image found in the reviewable.
        """
        from PIL import Image
        import PIL
        reviewable_thumbnail_path = self.reviewable_directory.system_path() + '/thumbnail.jpg'
        if os.path.exists(reviewable_thumbnail_path):
            return system.Filepath(reviewable_thumbnail_path)
        log.debug(f"Couldn't find pre-made thumbnail.. Generating thumbnail for {self.reviewable_directory}")
        image_extensions = (".png", ".jpg")
        for root, dirs, files in os.walk(self.reviewable_directory.system_path()):
            for file in files:
                if file.lower().endswith(image_extensions):
                    image_file = os.path.join(root, file)
                    try:
                        im = Image.open(system.Filepath(image_file).system_path())
                    except PIL.UnidentifiedImageError:
                        log.debug(f"Could not open {image_file}")
                        continue

                    self.generate_thumbnail(system.Filepath(image_file))
                    return system.Filepath(image_file)
        return None

    def get_subdirectories(self) -> List['system.Directory']:
        """
        Returns all subdirectories in the reviewable.
        :return: List of subdirectories in the reviewable.
        """
        return self.reviewable_directory.get_subdirectories()

    def generate_thumbnail(self, thumbnail_path: 'system.Filepath') -> system.Filepath:
        """
        Generates a thumbnail for the reviewable.
        :param thumbnail_path: Path to save the thumbnail to.
        :return: True if the thumbnail was generated successfully, False otherwise.
        """
        from PIL import Image, ImageFile  # type: ignore
        reviewable_thumbnail_path = self.reviewable_directory.system_path() + '/thumbnail.jpg'
        ImageFile.LOAD_TRUNCATED_IMAGES = True
        im = Image.open(thumbnail_path.system_path())
        rgb_im = im.convert('RGB')
        rgb_im.thumbnail((200, 200))
        rgb_im.save(reviewable_thumbnail_path)
        return system.Filepath(reviewable_thumbnail_path)


def reviewables_from_directory(directory: 'system.Directory') -> List['Reviewable']:
    """
    Factory function that returns all reviewables in a directory.
    :param directory: Directory to search for reviewables.
    :return: List of reviewables in the directory.
    """
    reviewables = []
    for subdirectory in directory.get_children_directories():
        basename = os.path.basename(subdirectory.directory_path)
        reviewable = SequenceReviewable(basename, subdirectory)
        reviewables.append(reviewable)
    return reviewables


class UsdReviewable(Reviewable):
    """
    Class for a Usd reviewable. Stores the all elements of a reviewable.
    """
    def __init__(self, reviewable_name: str, reviewable_directory: 'system.Directory', usd_asset: 'asset.Asset'):
        super().__init__(reviewable_name, reviewable_directory)
        self.reviewable_directory = reviewable_directory
        self.asset_type = asset.AssetType.USD
        self.usd_asset = usd_asset

    def __repr__(self) -> str:
        return f"USD Reviewable <{self.asset_name}> from " \
               f"<{self.reviewable_directory}>"

    def get_filepath(self) -> Union['system.Filepath', 'system.Directory']:
        """
        Gets the filepath of the asset.
        :return: Filepath of the asset.
        """
        usd_asset = self.usd_asset
        filepath = usd_asset.get_filepath().system_path()
        return filepath

    @classmethod
    def from_dict(cls, asset_dict: Dict[Any, Any]) -> Union[None, Any]:
        """
        Converts a dictionary to an asset.
        :param asset_dict: Dictionary to convert.
        :return: None
        """
        pass

    def to_dict(self) -> Dict[str, Any]:
        pass

    def get_thumbnail_image(self) -> Optional[system.Filepath]:
        """
        Recursively search a directory for images
        :return: Path to the first image found in the reviewable.
        """
        directory = self.reviewable_directory
        image_extensions = (".png", ".jpg")
        for root, dirs, files in os.walk(directory.system_path()):
            for file in files:
                if 'thumbnail' in file.lower():
                    if file.lower().endswith(image_extensions):
                        image_file = os.path.join(root, file)
                        return system.Filepath(image_file)
        return None

    def generate_thumbnail(self, thumbnail_path: 'system.Filepath') -> system.Filepath:
        """
        Generates a thumbnail for the reviewable.
        :param thumbnail_path: Path to save the thumbnail to.
        :return: True if the thumbnail was generated successfully, False otherwise.
        """
        pass