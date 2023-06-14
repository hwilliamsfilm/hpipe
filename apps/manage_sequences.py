import sys

import_list = [
    'Y:/_houdini_/scripts/',
    'Y:/_dev/',
    'Y:/_pipe/'
]

for p in import_list:
    sys.path.append(p)

from ui import sequenceManager

if __name__ == '__main__':
    sequenceManager.sequence_manager(sys.argv[1])