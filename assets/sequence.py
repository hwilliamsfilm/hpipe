"""
This module contains classes and functions for working with image sequences.
"""

import os
import shutil
import itertools
import re

from core.hutils import path
from core.hutils import logger
from core.hutils import timer
import core.hutils.path


logger.imported("sequence.py")


def _group_images_by_base(file_list):
    """
    Group image files by their basename. This function will return a dictionary of image sequences.
    :param file_list: list of image file paths
    :return: dict of image sequences
    """

    # Group files by the part before the frame number with regex
    pattern = re.compile(r'(.*)_(\d+)\.\w+$')

    # create dictionary of sequences
    sequences_dictionary = {}
    for file_path in file_list:
        match = pattern.match(file_path)
        if match:
            if match.group(1) in sequences_dictionary.keys():
                sequences_dictionary[match.group(1)].append(file_path)
            else:
                sequences_dictionary[match.group(1)] = [file_path]
    return sequences_dictionary


def _sequences_from_directory(directory, recursive=False):
    """
    Get image sequence objects from directory. This function will return a list of image sequence objects.
    :param directory: str directory path
    :param recursive: bool search recursively
    :return: list of image sequence objects
    """

    image_sequences = []
    file_list = []
    rejected = []

    # run directory verification
    directory = path.verify_directory(directory, create_if_not=False)

    if not directory:
        logger.warning('Error verifying directory: %s' % directory)
        return None

    # Collect all image files from the directory
    for root, dirs, files in os.walk(directory):
        # If not recursive, skip all subdirectories
        if not recursive:
            if dirs:
                continue

        for file in files:
            file_path = os.path.join(root, file)

            # Fix the path to be OS specific and use consistent separators
            file_path = path.fix_path(file_path)

            # Check if the file is an image (you can modify the condition based on your specific image formats)
            if file.endswith(('.png', '.jpg', '.jpeg', 'exr', '.tif', '.tiff', '.bmp', '.dpx', '.cin', '.dpx', '.tga')):
                file_list.append(file_path)
            else:
                rejected.append(file_path)

    # warn user of rejected files
    if rejected:
        logger.warning('Rejected files: %s' % rejected)

    # Sort the file list alphabetically to group by basename
    file_list.sort()

    # Group files by the part before the frame number with regex, returns a dictionary of image sequences
    sequences_dictionary = _group_images_by_base(file_list)

    # create and classify image sequence objects
    for k, v in sequences_dictionary.items():
        extension = path.get_extension(v[0])
        if 'deep' in k:
            continue
        if extension == 'exr':
            image_sequences.append(ExrImageSequence(v))
        if extension == 'jpg' or extension == 'png':
            image_sequences.append(GenericImageSequence(v))

    return image_sequences


class ImageSequence:
    """
    Base generic class for image sequences. This class should not be instantiated directly.
    This can be used to move image sequences around, or to get information about them.
    """
    def __init__(self, file_paths, is_temp=False):
        """
        :param file_paths: list of filepaths, should be sorted
        :param is_temp: bool is this a temporary sequence
        """
        self.file_paths = file_paths
        self.start_frame = file_paths[0]
        self.filename = self.get_filename()
        self.root = self.get_root()
        self.is_temp = is_temp

    def __repr__(self):
        return '<{format} sequence {name} -> {frame} Frames at path {path}'.format(name=self.filename,
                                                                                   frame=self.get_total_frames(),
                                                                                   format=self.get_extension(),
                                                                                   path=self.root)

    # GETTING THINGS
    def get_filepaths(self):
        """
        Method to get the filepaths of the image sequence
        :return: list of filepaths
        """
        return self.file_paths

    def get_date(self):
        """
        Method to get the date of the image sequence
        :return: str date
        """
        import datetime

        # get date in datetime str format
        date = datetime.datetime.fromtimestamp(os.path.getmtime(self.file_paths[0]))
        return date

    def get_filename(self):
        """
        Method to get the filename of the image sequence
        :return: str filename
        """
        import re

        # Get important information about image size
        first_image = self.file_paths[0]
        regex = r'(?P<root>.+)/(?P<filename>.+)_(?P<frame>\d+).(?P<extension>\w+)'
        match = re.match(regex, first_image, flags=re.IGNORECASE)
        filename = match.group('filename')
        return filename

    def get_total_frames(self):
        """
        Gets the total amount of frames in the image sequence
        :return: int total frames
        """
        if self.file_paths:
            return len(self.file_paths)
        else:
            return 0

    def get_root(self):
        """
        gets the root of the image sequence
        :return: str root path
        """
        import re
        # Get important information about image size
        first_image = self.file_paths[0]
        regex = r'(?P<root>.+)/(?P<filename>.+)_(?P<frame>\d+).(?P<extension>\w+)'
        match = re.match(regex, first_image, flags=re.IGNORECASE)
        root = match.group('root')
        return root

    def get_extension(self):
        """
        Gets file extension
        :return: str extension
        """
        return path.get_extension(self.file_paths[0])

    def get_start_frame(self):
        """
        Get start frame of sequence
        :return: int start frame
        """
        # TODO: Might it be easier to sort the filepaths with sorted() and then get the first frame from that?
        # something like this:
        # sorted(self.file_paths, key=lambda x: int(x.split('_')[-1].split('.')[0]))[0]

        start_frame = int(100000)
        for p in self.file_paths:
            frame = int(p.split('_')[-1].split('.')[0])
            start_frame = min(start_frame, frame)

        return start_frame

    def get_end_frame(self):
        """
        Get start frame of sequence
        :return: int end frame
        """
        end_frame = int(0)
        for p in self.file_paths:
            frame = int(p.split('_')[-1].split('.')[0])
            end_frame = max(end_frame, frame)
        return end_frame

    def is_temp(self):
        """
        Method to check if the sequence is temporary
        :return: bool is_temp
        """
        return self.is_temp

    def get_frame_size(self):
        """
        Method to get the frame size of the image sequence
        :return: tuple (width, height)
        """
        # NOTE: Might be better served by moving this to the generic image sequence subclass. I dont think exr's have
        # a size attribute or work with PIL

        from PIL import Image
        width, height = Image.open(self.file_paths[0]).size
        return width, height

    # DOING THINGS
    @timer.timing_decorator
    def copy(self, target_path, create_directories=True, move_files=False):
        """
        Creates a copy of sequence in destination
        :param target_path: str destination path
        :param create_directories: bool create directories if they don't exist
        :return: new sequence object
        """

        # verify target directory exists
        target_directory = path.verify_directory(target_path, create_if_not=create_directories)

        if target_directory:

            # get new filepaths
            target_filepaths = []

            for file_path in self.get_filepaths():

                file_name = file_path.split('/')[-1]
                destination_path = '{target_directory}/{filename}'.format(target_directory=target_directory, filename=file_name)

                # copy or move files
                if move_files:
                    shutil.move(file_path, destination_path)
                else:
                    shutil.copy(file_path, destination_path)

                target_filepaths.append(destination_path)

            # create new sequence object from the target directory
            new_sequence = _sequences_from_directory(target_directory)[0]

            return new_sequence

    def create_temp_files(self, sub_directory='temp'):
        """
        Function to create new sequence object of temp files
        :return: temp sequence object
        """

        # get root
        first_image = path.fix_path(self.file_paths[0])
        root_path = '/'.join(first_image.split('/')[:-1])

        destination_path = '{root}/{sub_directory}/'.format(root=root_path, sub_directory=sub_directory)

        logger.info('Creating temp files for {sequence} at {destination_path}'.format(sequence=self,
                                                                                      destination_path=destination_path))

        return self.copy(destination_path, create_directories=True)

        # TODO: I have no idea what this is doing. I think it's renaming the files to be sequential? But why...

        # newpaths = []
        # for f, p in enumerate(self.file_paths):
        #     f += self.get_start_frame()
        #     logger.info('{f} -> {p}'.format(f=f, p=p))
        #     root3 = '/'.join('_'.join(p.split('_')[:-1]).split('/')[:-1])
        #     fr = 'length = {length:03}'
        #
        #     newpath = '{root}/{filename}_{frame:04}.{ext}'.format(root=root3, filename=self.get_filename(),
        #                                                        frame=int(f), ext=self.get_extension())
        #     logger.info(newpath)
        #     os.rename(p, newpath)
        #     newpaths.append(newpath)
        #
        # if self.get_extension() == 'jpg' or self.get_extension() == 'png':
        #     return GenericImageSequence(newpaths, is_temp=True)
        # else:
        #     raise NotImplementedError

    def archive(self):
        """
        Method to archive the sequence. I don't like the idea of deleting things with code, so this will just move the
        sequence to the trash folder
        :return: bool True if successful
        """

        import datetime

        # replace the root path with the trash path
        new_root_path = path.fix_path(self.get_root().replace(r'Y:/projects', r'Y:/trash'))
        logger.debug(new_root_path)

        # create a new path with the current date and time
        new_root_path = '/'.join(new_root_path.split('/')[:-1] + [datetime.datetime.now().strftime("temp-%m-%d-%Y-%H-%M-%S")])

        # shutil.move(self.get_root(), new_root_path)
        logger.debug(new_root_path)

        archived_sequence = self.copy(new_root_path, create_directories=True, move_files=True)

        return archived_sequence


    def openInRV(self):
        import subprocess
        subprocess.Popen('rv {path}'.format(path=self.get_root()))


class GenericImageSequence(ImageSequence):
    '''
    Child class of Sequence for jpgs and pngs - this should also work for single frames
    '''

    # DOING THINGS
    @staticmethod
    def add_text(image,
                 font=None,
                 text='sample',
                 position=(0,0),
                 size=70,
                 color=(80, 80, 80, 100)):
        """
        Adds text to an image by burning it in.
        :param image: PIL image object to add text to
        :param font: str ttf font file path if none is provided, it will use the default font
        :param text: str text to add to the image
        :param position: tuple int position to add the text
        :param size: int size of the text
        :param color: tuple int color of the text
        :return: PIL image object with text burned in
        """

        from PIL import Image
        from PIL import ImageDraw
        from PIL import ImageFont
        from PIL import ImageOps

        if not font:
            font = ImageFont.truetype(r"Y:\_global_assets\fonts\Roboto-Bold.ttf", size)

        text_image = Image.new('RGBA', image.size, (255, 255, 255, 0))
        comp_image = ImageDraw.Draw(text_image)

        comp_image.text(position, text, fill=color,
               font=font, align='left')

        image_with_text = Image.alpha_composite(image, comp_image) # I had argument 2 to be comp_image from text_image

        return image_with_text


    @staticmethod
    def burn_matte(rgba_image, matte=2.35):
        """
        Burns in the matte to the PIL image object
        :param image: PIL image object to burn the matte into
        :param matte: float aspect ratio of the matte
        :return: PIL image object with the matte burned in
        """

        # create top matte bar. First create a box and composite it with the original image.
        top_bar = Image.new('RGBA', rgba_image.size, (255, 255, 255, 0))
        draw_top_bar = ImageDraw.Draw(top_bar)
        height_in_pixels_top = (height - (width * 1 / matte)) / 2
        draw_top_bar.rectangle((0, 0, width, 0 + height_in_pixels_top), fill=(30, 30, 30, 140))

        # composite the matte top bar with the original image
        rgba_image = Image.alpha_composite(rgba_image, box)

        # create bottom one
        bottom_bar = Image.new('RGBA', rgba_image.size, (255, 255, 255, 0))
        draw_bottom_bar = ImageDraw.Draw(bottom_bar)
        height_in_pixels_bottom = (height - (width * 1 / matte)) / 2
        draw_bottom_bar.rectangle((0, height - height_in_pixels_bottom, width, height), fill=(30, 30, 30, 140))

        # composite the matte bottom bar with the original image
        rgba_image = Image.alpha_composite(rgba_image, bottom_bar)

        return rgba_image

    @staticmethod
    def burn(image_path, matte=2.35, description='', date='', save=True):
        """
        Burns in the matte, description, and date to the image
        :param image_path: str path to the image to burn in
        :param matte: float aspect ratio of the matte
        :param description: str description to burn in
        :param date: str date to burn in
        :return: PIL image object with the matte, description, and date burned in
        """

        # import libraries
        from PIL import Image
        from PIL import ImageDraw
        from PIL import ImageFont
        from PIL import ImageOps
        import textwrap
        import datetime

        # open image
        rgba_image = Image.open(image_path).convert("RGBA")
        width, height = rgba_image.size

        # default fonts # TODO: make this a parameter
        font = ImageFont.truetype(r"Y:\_global_assets\fonts\Roboto-Bold.ttf", 60)
        font_small = ImageFont.truetype(r"Y:\_global_assets\fonts\Roboto-Bold.ttf", 20)

        # aadd matte if matte is not None
        if matte:
            rgba_image = burn_matte(rgba_image, matte)

        # add Date, Watermark
        rgba_image = add_text(rgba_image, font=font, text=date, position=(0,0), size=60, color=(255, 255, 255, 0))

        rgba_image = add_text(rgba_image, font=font_small, text='HUNTER WILLIAMS', position=(width * .9, height - 30),
                              size=20, color=(80, 80, 80, 100))

        # add Description
        description_text = Image.new('RGBA', combined.size, (255, 255, 255, 0))
        description_text_draw = ImageDraw.Draw(description_text)

        # custom text wrap
        description_text_draw.text((0, height - 60), textwrap.fill(description, width=80),
               fill=(80, 80, 80, 100),
               font=font_small)

        rgba_image = Image.alpha_composite(rgba_image, description_text)


        # save image if save is True, but return the image either way
        if save:
            try:
                rgba_image.convert('RGB').save(p)
                return rgba_image
            except Exception as e:
                logger.error("Cannot Save Image {0}: {1}".format(image_path, e))
                return None
        else:
            return rgba_image

    def burn_in(self, matte=2.35, description=''):
        import concurrent
        from concurrent import futures
        from utility import logger
        import datetime
        import re

        # setup multithreading
        executor = concurrent.futures.ProcessPoolExecutor(50)

        # loop through frames and collect submitted threads
        fut = []
        for frame in self.file_paths:
            logger.info(frame)
            #self.burn(frame, matte, description)
            foo = executor.submit(self.burn, frame, matte, description, datetime.datetime.now().strftime("%m/%d/%Y"))
            logger.warning(foo)
            fut.append(foo)

        # wait for threads
        futures.wait(fut)
        return True

    def create_slate(self, info, reference_frame=None):
        # import libraries
        from PIL import Image
        from PIL import ImageDraw
        from PIL import ImageFont
        from PIL import ImageOps
        import textwrap
        import datetime
        import re
        from core import constants as core_constants
        frame = self.get_start_frame() - 1
        logger.info(str(frame).rjust(4, '0'))

        slate_path = '{root}/{filename}_{frame}.{extension}'.format(root=self.get_root(),
                                                                  filename=self.get_filename(),
                                                                  frame=str(frame).rjust(4, '0'),
                                                                  extension=self.get_extension())

        logger.info(slate_path)
        path = core_constants.SLATE_PATH
        shutil.copy(path, slate_path)

        slate = Image.open(slate_path)
        size = self.get_frame_size()
        width, height = self.get_frame_size()


        # Show
        slate = self.add_text(slate, text=info['show'], position=(400, 70))

        # Version Name
        slate = self.add_text(slate, text=info['version'], position=(400, 210), color=(230, 80, 0, 150))

        # Date
        slate = self.add_text(slate, text=info['date'], position=(400, 350))

        # Date
        slate = self.add_text(slate, text=info['type'], position=(400, 480))

        # Description
        slate = self.add_text(slate, text=info['desc'], position=(400, 610), size=50)

        # Scope
        slate = self.add_text(slate, text=textwrap.fill(info['scope'], width=80), position=(400, 910), size=50)

        # Submission Note
        slate = self.add_text(slate, text=info['notes'], position=(400, 1210), size=50, color=(200, 100, 0, 150))

        # Submitting for: (feedback or approval)
        slate = self.add_text(slate, text=info['sub_type'], position=(1830, 70), color=(0, 100, 0, 100))

        ref = Image.open(self.file_paths[10])
        ref.thumbnail((1470,1400))
        slate.paste(ref, (2320, 80))

        slate = self.add_text(slate, text='HUNTER WILLIAMS', position=(2700, 985), size=60)

        slate = self.add_text(slate, text=info['shot_name'], position=(2700, 1060), size=60)

        slate = self.add_text(slate, text=info['seq_name'], position=(2700, 1220), size=60)

        slate = self.add_text(slate, text=info['scene_name'], position=(2700, 1300), size=60)

        slate = self.add_text(slate, text=info['frames'], position=(2700, 1620), size=60)

        slate = slate.resize(size)
        slate = slate.convert('RGB')
        slate.save(slate_path)
        self.file_paths.append(slate_path)
        return True

    def to_qt(self, output_path=None, parent=False):

        # import libraries
        from utility import logger
        import ffmpeg
        import re
        import time

        # start performance timer
        logger.debug('running QT')
        start = time.perf_counter()

        # get information about sequence
        # regex = r'(?P<root>.+)/(?P<filename>\w+)_(?P<frame>\d+)\.(?P<extension>\w+)'
        # match = re.match(regex, self.file_paths[0], flags=re.IGNORECASE)

        first_image = self.file_paths[0]
        first_image = utility.path.fix_path(first_image)
        root = '/'.join(first_image.split('/')[:-1])
        filename = '_'.join(first_image.split('/')[-1].split('_')[:-1])

        # root = match.group('root')
        # filename = match.group('filename')

        # get start frame
        start_frame = self.get_start_frame()
        logger.warning(start_frame)

        # create ffmpeg path
        ffmpeg_path = '{root}/{filename}_%04d.{extension}'.format(root=root, filename=filename, extension=self.get_extension())
        logger.info(ffmpeg_path)

        # generate output path if one not provided
        if not output_path:
            output_path = '{root}/{filename}.mp4'.format(root=self.get_root(), filename=self.get_filename())
            logger.info(output_path)

            if parent:
                parent_path = '/'.join(self.get_root().split('/')[:-2])
                output_path = '{root}/{filename}.mp4'.format(root=parent_path,
                                                             filename=self.get_filename())
                logger.info(output_path)

        logger.info(self.file_paths)
        # convert jpg to mp4
        stream = ffmpeg.input(ffmpeg_path, framerate=24, start_number=start_frame)

        # make sure the dimensions are even, or else it fails
        if self.get_extension() == 'png' or self.get_extension() == 'jpg':
            pad = {
                'width': 'ceil(iw/2)*2',
                'height': 'ceil(ih/2)*2'
            }
            stream = ffmpeg.filter_(stream, 'pad', **pad)
            stream = ffmpeg.filter_(stream, 'format', 'yuv420p')

        # run ffmpeg
        stream = ffmpeg.output(stream, output_path, video_bitrate="15M")
        logger.warning(ffmpeg_path)
        ffmpeg.run(stream)

        # end performance timer
        end = time.perf_counter()
        logger.info(f"{output_path} -> \n Completed in: {start - end:0.4f} seconds")

        return output_path

    def create_delivery(self, burn_in=True, doslate=False, deliver=True):
        import shutil
        import datetime
        from assets import projectFile
        from ui import popup
        import textwrap

        # create temp file sequence
        temp_sequence = self.create_temp_files()
        notes = ''

        if burn_in or doslate:
            from ui import slate
            notes = slate.multiline_text('Version Notes:')

        if burn_in:
            if not doslate:
                temp_sequence.burn_in(matte=2.35, description=textwrap.fill(notes, width=40))
            else:
                temp_sequence.burn_in(matte=2.35, description='Please see slate for notes.')

        if doslate:
            pf = projectFile.ProjectFile(self.file_paths[0])
            shot = pf.get_shot()
            proj = pf.get_project()

            logger.info(notes)

            info = {
                'show': proj.name,
                'version': self.get_filename(),
                'date': datetime.datetime.now().strftime("%Y-%m-%d"),
                'type': 'Media',
                'desc': 'N/A',
                'scope': 'N/A',
                'notes': notes,
                'sub_type': 'Approval',
                'shot_name': shot.name,
                'seq_name': proj.name,
                'scene_name': proj.name,
                'frames': '{0}-{1}'.format(self.get_start_frame(), self.get_end_frame())
            }

            temp_sequence.create_slate(info)

        # temp_sequence.create_slate()
        deliverable = temp_sequence.to_qt(parent=True)
        temp_sequence.archive()

        # add to project deliveries
        if deliver:
            pf = projectFile.ProjectFile(deliverable)
            shot = pf.get_shot()
            proj = pf.get_project()
            root = proj.get_delivery_path()
            filename = deliverable.split('/')[-1]
            filepath = '{root}/{date}/{filename}'.format(root=root,
                                                         date=datetime.datetime.now().strftime("%Y-%m-%d"),
                                                         filename=filename)
            dest = '{root}/{date}/'.format(root=root, date=datetime.datetime.now().strftime("%Y-%m-%d"))
            if not os.path.isdir(dest):
                os.makedirs(dest)
            shutil.copy(deliverable, filepath)


    # TODO please refactor
    @staticmethod
    def create_contact_sheet(sequences, output_path=None):
        import ffmpeg
        import re
        from utility import logger
        import PIL
        from PIL import Image

        # Get important information about image size
        first_image = sequences[0].filepaths[0]
        # loading the image
        img = PIL.Image.open(first_image)
        # fetching the dimensions
        wid, hgt = img.size

        num_images = len(sequences[0].get_filepaths())

        regex = r'(?P<root>.+)/(?P<filename>\w+)_(?P<frame>\d+)\.(?P<extension>\w+)'
        match = re.match(regex, first_image, flags=re.IGNORECASE)
        root = match.group('root')
        dest = '{root}/contactSheetTemp/'.format(root=root)
        os.makedirs(dest)

        for seq in sequences:
            logger.debug('Starting...{0}'.format(seq))
            seq.copy(dest)
            logger.debug('merp')
            logger.debug(seq.get_filepaths()[0])

        newpathlist = list(path.roundrobin(sequences[0].get_filepaths(), sequences[1].get_filepaths(), sequences[2].get_filepaths(),
                                      sequences[3].get_filepaths()))

        temppathlist = []
        for f, p in enumerate(newpathlist):
            f += 1000
            logger.info('{f} -> {p}'.format(f=f, p=p))
            root3 = '/'.join('_'.join(p.split('_')[:-1]).split('/')[:-1])

            newpath = '{root}/temp_{frame}.jpg'.format(root=root3, frame=int(f))
            logger.info(newpath)
            os.rename(p, newpath)
            temppathlist.append(newpath)

        regex = r'(?P<root>.+)/(?P<filename>\w+)_(?P<frame>\d+)\.(?P<extension>\w+)'
        match = re.match(regex, temppathlist[0], flags=re.IGNORECASE)
        root2 = match.group('root')
        filename2 = match.group('filename')

        # # create path
        src_path = '{root}/{filename}_%04d.jpg'.format(root=root2, filename=filename2)

        logger.info(src_path)

        if not output_path:
            output_path = '{root}/contact_sheet_01_%04d.jpg'.format(root=root)

        stream = ffmpeg.input(src_path, start_number='1000')
        stream = ffmpeg.filter_(stream, 'scale', size='{0}:{1}'.format(int(wid/2), int(hgt/2)))
        stream = ffmpeg.filter_(stream, 'tile', '2x2')
        stream = ffmpeg.output(stream, output_path, start_number='1000')
        ffmpeg.run(stream)

        jpgList = []
        for i in range(num_images):
            frame = i+1000
            myPath = '{root}/contact_sheet_01_{frame}.jpg'.format(root=root, frame=frame)
            jpgList.append(myPath)
            logger.info(myPath)

        return GenericImageSequence(jpgList)


class ExrImageSequence(ImageSequence):
    '''
    Child class of Sequence for EXRs - this should also work for single frames
    '''


    # GENERAL PURPOSE EXR METHODS
    #TODO Might need to be class methods? if so then id have to create an image class for single frame

    @staticmethod
    def get_info(exr_path):
        import OpenEXR
        import re

        file = OpenEXR.InputFile(exr_path)

        regex = r'(?P<channel>\w+)\.(?P<color>\w+)$'

        chan = set()
        header = file.header()
        for k in header['channels'].keys():
            match = re.match(regex, k, flags=re.IGNORECASE)
            if match:
                chan.add(match.group('channel'))
            else:
                chan.add(k)

        dict = {}
        dict['channels'] = chan
        dict['exr_file'] = file
        dict['header'] = header
        return dict

    @staticmethod
    def encode_channel(exr_file, c_name):
        """
        class to do a basic linear to rec709 conversion. its not perfect, but does the trick for previews
        :param exr_file:
        :param c_name:
        :return:
        """
        import array
        import Imath

        pixel_type = Imath.PixelType(Imath.PixelType.FLOAT)

        c = exr_file.channel(c_name, pixel_type)
        c_array = array.array('f', c)

        # do srgb encoding
        for i in range(len(c_array)):
            if c_array[i] <= 0.0031308:
                c_array[i] = (c_array[i] * 12.92) * 255.0
            else:
                c_array[i] = (1.055 * (c_array[i] ** (1.0 / 2.4)) - 0.055) * 255.0
        return c_array

    @staticmethod
    def exr_to_jpg(exr_path, jpg_path, channel_name='beauty'):
        """
        static method to convert single exr image to single jpg image
        :param exr_path:
        :param jpg_path:
        :param channel_name:
        :return:
        """
        import OpenEXR
        import re
        from PIL import Image
        import array
        import Imath
        import time
        from utility import logger

        # start performance timer
        start = time.perf_counter()

        # get exr info
        info = ExrImageSequence.get_info(exr_path)
        file = info['exr_file']
        header = info['header']

        # edge case channel names
        if channel_name == 'beauty' or channel_name == "RGB":
            channels = ['R', 'G', 'B']
        else:
            channels = [c for c in header['channels'].keys() if channel_name in c][:3]

        if not channels or channel_name == '':
            channels = ['R', 'G', 'B']

        # get frame size
        datawindow = file.header()['dataWindow']
        size = (datawindow.max.x - datawindow.min.x + 1, datawindow.max.y - datawindow.min.y + 1)

        # convert
        rgbf = [Image.frombuffer("F", size, ExrImageSequence.encode_channel(file, channels[0]).tobytes())]
        rgbf.append(Image.frombuffer("F", size, ExrImageSequence.encode_channel(file, channels[1]).tobytes()))
        rgbf.append(Image.frombuffer("F", size, ExrImageSequence.encode_channel(file, channels[2]).tobytes()))

        # color space conversion
        rgb8 = [im.convert("L") for im in rgbf]
        Image.merge("RGB", rgb8).save(jpg_path, "JPEG", quality=95)

        # end performance timer
        end = time.perf_counter()
        logger.info(f"{jpg_path} -> \n Completed in: {start - end:0.4f} seconds")
        return jpg_path

    # DOING THINGS
    def to_jpg(self, channel="RGB"):
        """
        Method to convert EXR sequence to a JPG sequence
        :param channel:
        :return:
        """
        import concurrent
        from concurrent import futures
        from utility import logger
        import re

        # setup multithreading
        executor = concurrent.futures.ProcessPoolExecutor(50)

        # loop through frames and collect submitted threads
        fut = []
        filepaths = []
        # get information about sequence
        regex = r'(?P<root>.+)/(?P<filename>\w+)_(?P<frame>\d+)\.(?P<extension>\w+)'

        for f in self.file_paths:
            logger.info(f)
            match = re.match(regex, f, flags=re.IGNORECASE)
            root = match.group('root')
            frame = match.group('frame')

            # create jpg naming convention
            jpg_path = '{root}/{channel}/{channel}_{frame}.jpg'.format(root=root, frame=frame, channel=channel)
            fut.append(executor.submit(self.exr_to_jpg, f, jpg_path, channel))
            filepaths.append(jpg_path)

        # get filename info
        regex = r'(?P<root>.+)/(?P<filename>.+)_(?P<frame>\d+).(?P<extension>\w+)'
        match = re.match(regex, filepaths[0], flags=re.IGNORECASE)
        name = match.group('filename')

        # wait for threads
        futures.wait(fut)

        logger.info(filepaths)
        return GenericImageSequence(filepaths)



