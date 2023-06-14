import os
import subprocess
from core.hutils import path


def open_dir(p):
    subprocess.call(["open", path.fix_path(p, sep='//')])
