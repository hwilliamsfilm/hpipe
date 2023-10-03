import os
from typing import *

OIIO = False
try:
    import oiio
    from oiio import ImageBuf, ImageSpec, ImageOutput
    OIIO_LOADED = True
except ImportError:
    pass
try:
    import OpenIMageIO as oiio
    from OpenImageIO import ImageBuf, ImageSpec, ImageOutput
    OIIO_LOADED = True
except ImportError:
    pass


from assets import asset
from core.hutils import logger, system
from core import constants

if TYPE_CHECKING:
    pass

log = logger.setup_logger()
log.debug("ImageSequence.py loaded")


class GenericImageSequence(asset.Asset):
    """
    Class for an image sequence. Stores related images as a list of filepaths.
    """
    def __init__(self, filepaths: List['system.Filepath'], asset_name: str = '',
                 start_frame: int = 0, end_frame: int = 0):
        super().__init__(asset_name)

        self.filepaths = filepaths
        self.sort_filepaths()

        if start_frame == 0:
            start_frame = self.get_start_frame()

        if end_frame == 0:
            end_frame = self.get_end_frame()

        self.start_frame = start_frame
        self.end_frame = end_frame
        self.asset_type = asset.AssetType.IMAGE_SEQUENCE

    def __repr__(self) -> str:
        return f"ImageSequence {self.get_start_frame()}-{self.get_end_frame()} @ <{self.asset_name}> " \
               f"from <{self.filepaths[0].filepath_path}>"

    def to_dict(self) -> Dict[str, Any]:
        """
        Converts the asset to a dictionary.
        :return: Dictionary representation of the asset.
        """
        return {
            'asset_name': self.asset_name,
            'asset_type': self.asset_type.value,
            'start_frame': self.start_frame,
            'end_frame': self.end_frame,
            'filepaths': [filepath.filepath_path for filepath in self.filepaths]
        }

    @classmethod
    def from_dict(asset_dict: Dict[Any, Any]) -> 'GenericImageSequence':
        """
        Converts a dictionary to an asset.
        :param asset_dict: Dictionary to convert.
        :return: None
        """
        return GenericImageSequence(asset_dict['filepaths'], asset_dict['asset_name'],
                                    asset_dict['start_frame'], asset_dict['end_frame'])

    def get_filepath(self) -> 'system.Filepath':
        """
        Gets the filepath of the image sequence.
        :return: Filepath of the image sequence.
        """
        return self.get_parent_directory()

    def get_start_frame(self) -> int:
        """
        Returns the start frame of the image sequence.
        :return: int start frame
        """
        if len(self.filepaths) == 0:
            return -1
        return self.filepaths[0].get_frame_number()

    def get_end_frame(self) -> int:
        """
        Returns the end frame of the image sequence.
        :return: int end frame
        """
        if len(self.filepaths) == 0:
            return -1
        return self.filepaths[-1].get_frame_number()

    def get_extension(self) -> str:
        """
        Returns the extension of the image sequence.
        """
        return self.filepaths[0].get_extension()

    def get_total_frames(self) -> int:
        """
        Returns the total number of frames in the image sequence.
        """
        return self.end_frame - self.start_frame + 1

    def get_parent_directory(self) -> 'system.Directory':
        """
        Returns the parent directory of the image sequence.
        """
        if len(self.filepaths) == 0:
            raise ValueError("Image sequence has no parent directory.")
        return self.filepaths[0].get_parent_directory()

    def get_basename(self) -> str:
        """
        Returns the basename of the image sequence.
        """
        if len(self.filepaths) == 0:
            raise ValueError("Image sequence has no basename.")
        return self.filepaths[0].get_filename()

    def sort_filepaths(self) -> bool:
        """
        Sorts the filepaths in the image sequence by frame number.
        :return: True if successful, False if not
        """
        self.filepaths.sort(key=lambda x: x.get_frame_number())
        return True

    def get_metadata(self) -> dict:
        """
        Returns the metadata of the image sequence.
        """
        spec = oiio.ImageInput.open(self.filepaths[0].filepath_path).spec()
        metadata = spec
        return metadata

    def archive(self, target_directory: 'system.Directory' = system.Directory(r'.//')) -> 'GenericImageSequence':
        """
        Archives the image sequence to a zip file.
        """

        import datetime
        import shutil
        import uuid

        if target_directory.directory_path == '.' or target_directory.directory_path == './':
            target_directory = system.Directory(constants.RECYCLE_BIN)

        parent_directory = self.get_parent_directory()
        current_date = datetime.datetime.now().strftime("%Y-%m-%d")
        target_directory = system.Directory(f"{target_directory.directory_path}/"
                                            f"{current_date}/"
                                            f"{self.get_basename()}/"
                                            f"{uuid.uuid4()}")

        if not os.path.exists(target_directory.directory_path):
            os.makedirs(target_directory.directory_path)

        log.debug(f"Archiving {self} to {target_directory}")

        if not os.path.exists(target_directory.directory_path):
            raise ValueError(f"Target directory does not exist: {target_directory}")

        if not os.path.exists(parent_directory.directory_path):
            log.debug(f"image_files: {self.filepaths}")
            raise ValueError(f"Parent directory does not exist: {parent_directory.directory_path}")

        if not os.path.exists(self.filepaths[0].filepath_path):
            raise ValueError(f"First image in sequence does not exist: {self.filepaths[0]}")

        shutil.move(parent_directory.directory_path, target_directory.directory_path)
        new_sequence = sequences_from_directory(target_directory)[0]
        return new_sequence

    def to_mp4(self, target_directory: 'system.Directory' = system.Directory(r'.')) -> 'system.Filepath':
        """
        Converts the image sequence to a mp4 video.
        :returns: the target filepath
        """

        if target_directory.directory_path == '.' or target_directory.directory_path == './':
            target_directory = self.get_parent_directory().get_parent_directory()

        log.info(f'Target Directory: {target_directory.directory_path}')
        target_file = system.Filepath(f"{target_directory.directory_path}/{self.get_basename()}.mp4")

        if os.path.exists(target_file.filepath_path):
            log.warning(f"File already exists: {target_file}")
            return target_file

        sequence_to_video(self, target_file)

        return target_file


class ExrImageSequence(GenericImageSequence):
    """
    Class for an exr image sequence. Stores related images as a list of filepaths.
    """
    def __init__(self, filepaths: List['system.Filepath'], asset_name: str = '',
                 start_frame: int = 0, end_frame: int = 0):
        super().__init__(filepaths, asset_name, start_frame, end_frame)

    def __repr__(self) -> str:
        return f"EXR ImageSequence {self.get_start_frame()}-{self.get_end_frame()} @ <{self.asset_name}> " \
               f"from <{self.get_parent_directory().directory_path}>"

    def to_mp4(self, target_directory: 'system.Directory' = system.Directory(r'.//')) -> 'system.Filepath':
        raise NotImplementedError("EXR to MP4 conversion not implemented yet.")


class JpgImageSequence(GenericImageSequence):
    """
    Class for a jpg image sequence. Stores related images as a list of filepaths.
    """
    def __init__(self, filepaths: List['system.Filepath'], asset_name: str = '',
                 start_frame: int = 0, end_frame: int = 0):
        super().__init__(filepaths, asset_name, start_frame, end_frame)

    def __repr__(self) -> str:
        return f"JPG ImageSequence {self.get_start_frame()}-{self.get_end_frame()} @ <{self.asset_name}> " \
               f"from <{self.get_parent_directory().directory_path}>"


class PngImageSequence(GenericImageSequence):
    """
    Class for a png image sequence. Stores related images as a list of filepaths.
    """
    def __init__(self, filepaths: List['system.Filepath'], asset_name: str = '',
                 start_frame: int = 0, end_frame: int = 0):
        super().__init__(filepaths, asset_name, start_frame, end_frame)

    def __repr__(self) -> str:
        return f"PNG ImageSequence {self.get_start_frame()}-{self.get_end_frame()} @ <{self.asset_name}> " \
               f"from <{self.filepaths[0].filepath_path}>"


def sequence_factory(file_paths: List['system.Filepath'], file_name: str = '') -> GenericImageSequence:
    """
    Factory function for creating image sequences from a list of filepaths.
    :param file_paths: List of filepaths
    :param file_name: Name of the image sequence
    :return: Image sequence
    """
    file_path_extension = file_paths[0].get_extension()
    if file_path_extension == 'exr':
        return ExrImageSequence(file_paths, file_name)
    elif file_path_extension == 'jpg':
        return JpgImageSequence(file_paths, file_name)
    elif file_path_extension == 'png':
        return PngImageSequence(file_paths, file_name)
    else:
        raise ValueError(f"Could not create image sequence from {file_paths}.")


def sequences_from_directory(directory: system.Directory, temp: bool = True) -> List[GenericImageSequence]:
    """
    Returns a list of image sequences from a directory. We assume that within the directory, there are subdirectories
    that contain image sequences. So each subdirectory is a version where multiple image sequences are stored.
    :param directory: Directory to search for image sequences
    :param temp: Whether to include temp files in the search
    :return: List of image sequences
    """
    log.debug(directory.directory_path)
    directory_sequences = []

    sequences_dictionary: dict[str, List[system.Filepath]] = {}
    for root, dirs, files in os.walk(directory.directory_path):
        for file in files:
            basename = '_'.join(file.split('_')[:-1])
            full_path = os.path.join(root, file)

            if full_path == '' or full_path is None:
                log.warning(f"Could not find full path for {file}. Skipping..")
                continue

            if not temp and 'temp' in full_path or 'tmp' in full_path:
                log.warning(f"Skipping temp file {file}.")
                continue

            if system.Filepath(full_path).get_extension() not in ['exr', 'jpg', 'png']:
                log.warning(f"{file} is not a valid image file. Skipping..")
                continue

            if basename not in sequences_dictionary:
                sequences_dictionary[basename] = []
                sequences_dictionary[basename].append(system.Filepath(full_path))
            else:
                sequences_dictionary[basename].append(system.Filepath(full_path))

    for sequence_key, sequence_value in sequences_dictionary.items():
        if sequence_key == '':
            log.warning(f"Could not find sequence key for {sequence_value}. Skipping..")
            continue

        if sequence_factory(sequence_value, sequence_key) in directory_sequences:
            continue

        directory_sequences.append(sequence_factory(sequence_value, sequence_key))

    log.info(f"Found {len(directory_sequences)} sequences in {directory.directory_path}")

    return directory_sequences


def sequence_to_video(image_sequence: 'GenericImageSequence', output_path: 'system.Filepath') -> bool:
    """
    Converts the image sequence to a video.
    :param image_sequence: Image sequence to convert
    :param output_path: Output path for the video
    :return: True if successful, False if not
    """

    import ffmpeg  # type: ignore

    first_image = image_sequence.filepaths[0]
    root = first_image.get_parent_directory().directory_path
    filename = '_'.join(first_image.basename.split('_')[:-1])

    start_frame = image_sequence.get_start_frame()

    ffmpeg_path = '{root}/{filename}_%04d.{extension}'.format(root=root, filename=filename,
                                                              extension=image_sequence.get_extension())

    stream = ffmpeg.input(ffmpeg_path, framerate=24, start_number=start_frame)

    if image_sequence.get_extension() == 'png' or image_sequence.get_extension() == 'jpg':
        pad = {
            'width': 'ceil(iw/2)*2',
            'height': 'ceil(ih/2)*2'
        }
        stream = ffmpeg.filter_(stream, 'pad', **pad)
        stream = ffmpeg.filter_(stream, 'format', 'yuv420p')

    stream = ffmpeg.output(stream, output_path.filepath_path, loglevel="error", video_bitrate="15M")

    try:
        ffmpeg.run(stream)
    except ffmpeg.Error as e:
        log.error(e.stderr)
        return False

    return True
