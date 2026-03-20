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

# Supported thumbnail source extensions (checked by get_thumbnail_image).
THUMBNAIL_EXTENSIONS = (".jpg", ".jpeg", ".png", ".tif", ".tiff", ".tga", ".exr", ".dpx")


def _load_hdr_as_rgb(filepath: str):
    """
    Load an HDR image (EXR, DPX, …) and return a Pillow RGB image suitable for
    JPEG saving.  Applies a simple per-channel Reinhard tone-map then gamma-
    encodes to sRGB.

    Tries OpenImageIO first; falls back to a numpy+Pillow path.
    Returns None if the image cannot be loaded.
    """
    # ── OIIO path ────────────────────────────────────────────────────────
    try:
        import OpenImageIO as oiio  # type: ignore
        import numpy as np
        buf = oiio.ImageBuf(filepath)
        spec = buf.spec()
        pixels = buf.get_pixels(oiio.FLOAT)
        if pixels is None:
            raise RuntimeError("OIIO returned no pixels")
        arr = np.array(pixels, dtype=np.float32)
        # Keep only first 3 channels (drop alpha / extra AOVs)
        if arr.ndim == 3 and arr.shape[2] >= 3:
            arr = arr[:, :, :3]
        arr = _reinhard(arr)
        arr = np.clip(arr * 255, 0, 255).astype(np.uint8)
        from PIL import Image  # type: ignore
        return Image.fromarray(arr, mode="RGB")
    except Exception as e:
        log.debug(f"OIIO load failed for {filepath}: {e}")

    # ── numpy+Pillow path (requires Pillow >= 9.1 for EXR, or imageio) ──
    try:
        import numpy as np
        from PIL import Image  # type: ignore
        pil_img = Image.open(filepath)
        arr = np.array(pil_img, dtype=np.float32)
        if arr.ndim == 2:
            arr = np.stack([arr] * 3, axis=-1)
        elif arr.shape[2] == 4:
            arr = arr[:, :, :3]
        arr = _reinhard(arr)
        arr = np.clip(arr * 255, 0, 255).astype(np.uint8)
        return Image.fromarray(arr, mode="RGB")
    except Exception as e:
        log.debug(f"Pillow HDR load failed for {filepath}: {e}")

    return None


def _reinhard(arr):
    """Per-channel Reinhard tone-map: x / (1 + x).  Assumes float input."""
    import numpy as np
    arr = np.maximum(arr, 0.0)
    return arr / (1.0 + arr)


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


class ProjectFileReviewable(Reviewable):
    """
    Lightweight adapter that lets a :class:`~hpipe.assets.projectFile.GenericProjectFile`
    appear in the Output Viewer grid alongside image-based reviewables.

    Project files (.hip, .nk, etc.) have no image data, so thumbnails always
    fall back to the default placeholder.
    """

    def __init__(self, project_file: 'asset.Asset'):
        from hpipe.assets import projectFile
        if not isinstance(project_file, projectFile.GenericProjectFile):
            raise TypeError(f"Expected GenericProjectFile, got {type(project_file)}")
        directory = project_file.filepath.get_parent_directory()
        name = project_file.asset_name or project_file.filepath.get_filename()
        super().__init__(name, directory)
        self.project_file = project_file
        self.asset_type = asset.AssetType.PROJECT_FILE

    def __repr__(self) -> str:
        return f"ProjectFileReviewable <{self.asset_name}> @ {self.project_file.filepath}"

    def get_filepath(self) -> 'system.Filepath':
        return self.project_file.filepath

    @classmethod
    def from_dict(cls, asset_dict: Dict[Any, Any]) -> Union[None, Any]:
        pass

    def to_dict(self) -> Dict[str, Any]:
        return self.project_file.to_dict()

    def get_thumbnail_image(self) -> Optional[system.Filepath]:
        # Project files have no image data — always use the fallback icon.
        return None

    def generate_thumbnail(self, thumbnail_path: 'system.Filepath') -> Optional[system.Filepath]:
        return None

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
        Return the thumbnail for this reviewable.

        Strategy (in order):
        1. Return a pre-cached ``thumbnail.jpg`` if one already exists.
        2. Walk the reviewable directory for a supported image file, generate
           a 200×200 JPEG thumbnail, and return that path.

        Supported source extensions: jpg, jpeg, png, tif, tiff, exr, dpx, tga.
        EXR files are tone-mapped (simple Reinhard) before saving.
        """
        reviewable_thumbnail_path = (
            self.reviewable_directory.system_path() + "/thumbnail.jpg"
        )
        if os.path.exists(reviewable_thumbnail_path):
            return system.Filepath(reviewable_thumbnail_path)

        log.debug(
            f"No cached thumbnail — generating for {self.reviewable_directory}"
        )

        # Preferred non-EXR formats first (fast to open), then EXR.
        preferred = (".jpg", ".jpeg", ".png", ".tif", ".tiff", ".tga")
        fallback = (".exr", ".dpx")

        def _first_match(extensions):
            for root, _dirs, files in os.walk(
                self.reviewable_directory.system_path()
            ):
                for f in sorted(files):
                    if f.lower().endswith(extensions):
                        return os.path.join(root, f)
            return None

        source = _first_match(preferred) or _first_match(fallback)
        if source is None:
            return None

        fp = system.Filepath(source)
        saved = self.generate_thumbnail(fp)
        if saved and os.path.exists(saved.system_path()):
            return saved
        # generate_thumbnail may have failed (e.g. corrupt file); fall back to
        # returning the source path so QImage can still try to load it.
        return fp

    def get_subdirectories(self) -> List['system.Directory']:
        """
        Returns all subdirectories in the reviewable.
        :return: List of subdirectories in the reviewable.
        """
        return self.reviewable_directory.get_subdirectories()

    def generate_thumbnail(self, thumbnail_path: 'system.Filepath') -> Optional[system.Filepath]:
        """
        Generate a 200×200 JPEG thumbnail from *thumbnail_path* and write it
        next to the reviewable directory as ``thumbnail.jpg``.

        Handles LDR formats (jpg, png, tif, tga) via Pillow and HDR/EXR via
        OpenImageIO when available, falling back to a numpy Reinhard tone-map
        via Pillow if OIIO is absent.

        :param thumbnail_path: Source image filepath.
        :return: Filepath of the saved thumbnail, or None on failure.
        """
        save_path = self.reviewable_directory.system_path() + "/thumbnail.jpg"
        ext = thumbnail_path.get_extension().lower()

        try:
            if ext in ("exr", "dpx"):
                img_rgb = _load_hdr_as_rgb(thumbnail_path.system_path())
            else:
                from PIL import Image, ImageFile  # type: ignore
                ImageFile.LOAD_TRUNCATED_IMAGES = True
                pil_img = Image.open(thumbnail_path.system_path())
                img_rgb = pil_img.convert("RGB")

            if img_rgb is None:
                return None

            img_rgb.thumbnail((200, 200))
            img_rgb.save(save_path, "JPEG", quality=85)
            return system.Filepath(save_path)

        except Exception as e:
            log.debug(f"generate_thumbnail failed for {thumbnail_path}: {e}")
            return None


def reviewables_from_directory(directory: 'system.Directory') -> List['Reviewable']:
    """
    Factory function that returns all reviewables in a directory.

    Returns an empty list (instead of raising) when *directory* does not
    exist on disk.

    :param directory: Directory to search for reviewables.
    :return: List of reviewables in the directory.
    """
    if not directory.exists():
        log.warning(f"Directory does not exist, returning empty list: {directory.directory_path}")
        return []

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
        Recursively search a directory for a thumbnail image.
        :return: Path to the first image found in the reviewable.
        """
        directory = self.reviewable_directory
        for root, _dirs, files in os.walk(directory.system_path()):
            for file in sorted(files):
                if "thumbnail" in file.lower() and file.lower().endswith(THUMBNAIL_EXTENSIONS):
                    return system.Filepath(os.path.join(root, file))
        return None

    def generate_thumbnail(self, thumbnail_path: 'system.Filepath') -> system.Filepath:
        """
        Generates a thumbnail for the reviewable.
        :param thumbnail_path: Path to save the thumbnail to.
        :return: True if the thumbnail was generated successfully, False otherwise.
        """
        pass