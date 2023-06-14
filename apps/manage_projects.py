import sys

import_list = [
    'Y:/_houdini_/scripts/',
    'Y:/_dev/',
    'Y:/_pipe/',
    '/Volumes/hlw01/_pipe/'
]

for p in import_list:
    sys.path.append(p)

from ui import projManager

projManager.db_manager()

