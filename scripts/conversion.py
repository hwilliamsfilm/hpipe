import sys

import_list = [
    'Y:/_houdini_/scripts/',
    'Y:/_dev/',
    'Y:/_pipe/'
]

for p in import_list:
    sys.path.append(p)

from utility import path


def convert_sequence(dir, type):
    seq = path.get_image_sequences(dir)
    if type == 'delivery_overlay':
        seq[0].create_delivery(burn_in=True, doslate=True)
    if type == 'delivery':
        seq[0].create_delivery(burn_in=False, doslate=True)
    if type == 'preview':
        seq[0].create_delivery(burn_in=False, doslate=False, deliver=False)
    if type == '':
        seq[0].create_delivery(burn_in=True, doslate=True, deliver=False)

if __name__ == '__main__':
    from utility import logger
    logger.info(sys.argv)
    convert_sequence(sys.argv[1], sys.argv[2])