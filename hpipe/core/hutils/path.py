"""
Path utilities.
"""


def fix_path(old_path: str, seperator: str = '/') -> str:
    """
    Fixes a path to be the correct format for the current OS
    :param old_path: Path to fix
    :param seperator: Seperator to use for the path
    :return: Fixed path
    """
    _path = old_path.replace('\\', '/')
    _path = _path.replace('\\\\', '/')
    _path = _path.replace('//', '/')

    if _path.endswith('/'):
        _path = _path[:-1]

    _path = _path.replace('/', seperator)

    new_path = _path
    return new_path
