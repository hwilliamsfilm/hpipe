from core.hutils import logger
import os
import Imath

def exr_to_jpg(self, filepath, root):
    from utility import path

    f = path.fix_path(filepath)
    if self.extension() != "exr":
        return

    if 'deep' in f:
        logger.warning('SKIPPING: Deep image')
        return None

    path = 'foo'

    # check if exists
    if os.path.exists(path):
        logger.warning('Skipping: {0}'.format(path))
        return path


    return path


def convert_exr_to_jpg(exrpath, jpgpath, channel_name='beauty'): #f path
    import OpenEXR
    import re
    from PIL import Image
    import array
    from pprint import pprint
    import time

    tic = time.perf_counter()
    def encode_channel(exr_file, c_name):
        c = exr_file.channel(c_name, pixel_type)
        c_array = array.array('f', c)

        # do srgb encoding
        for i in range(len(c_array)):
            if c_array[i] <= 0.0031308:
                c_array[i] = (c_array[i] * 12.92) * 255.0
            else:
                c_array[i] = (1.055 * (c_array[i] ** (1.0 / 2.4)) - 0.055) * 255.0
        return c_array

    file = OpenEXR.InputFile(exrpath) # get openexr object
    regex = r'(?P<channel>\w+)\.(?P<color>\w+)$'

    chan = set()
    header = file.header()

    for k in header['channels'].keys():
        match = re.match(regex, k, flags=re.IGNORECASE)
        if match:
            chan.add(match.group('channel'))
        else:
            chan.add(k)

    if channel_name == 'beauty':
        channels = ['R', 'G', 'B']
    else:
        channels = [c for c in header['channels'].keys() if channel_name in c][:3]

    if not channels or channel_name == '':
        channels = ['R', 'G', 'B']

    pixel_type = Imath.PixelType(Imath.PixelType.FLOAT) # pixel type float
    datawindow = file.header()['dataWindow']
    size = (datawindow.max.x - datawindow.min.x + 1, datawindow.max.y - datawindow.min.y + 1)

    rgbf = [Image.frombuffer("F", size, encode_channel(file, channels[0]).tobytes())]
    rgbf.append(Image.frombuffer("F", size, encode_channel(file, channels[1]).tobytes()))
    rgbf.append(Image.frombuffer("F", size, encode_channel(file, channels[2]).tobytes()))

    rgb8 = [im.convert("L") for im in rgbf]
    Image.merge("RGB", rgb8).save(jpgpath, "JPEG", quality=95)
    toc = time.perf_counter()
    logger.info(f"{jpgpath}: {toc - tic:0.4f} seconds")

    return jpgpath