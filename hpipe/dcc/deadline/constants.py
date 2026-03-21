"""
Constants for Deadline submission.
"""
import os

# ── Deadline executable ───────────────────────────────────────────────────────
# Searches common install locations; override with DEADLINE_PATH env var.
_DEFAULT_DEADLINE_PATHS = [
    r"C:\Program Files\Thinkbox\Deadline10\bin\deadlinecommand.exe",
    r"C:\Program Files\Thinkbox\Deadline\bin\deadlinecommand.exe",
    r"/opt/Thinkbox/Deadline10/bin/deadlinecommand",
    r"/opt/Thinkbox/Deadline/bin/deadlinecommand",
    r"/Applications/Thinkbox/Deadline10/bin/deadlinecommand",
]


def get_deadline_command() -> str:
    """
    Return the absolute path to the ``deadlinecommand`` executable.

    Resolution order:
    1. ``DEADLINE_PATH`` environment variable (pointing to *bin* dir or the exe)
    2. First match from :data:`_DEFAULT_DEADLINE_PATHS`

    :raises FileNotFoundError: if no executable is found.
    """
    env = os.environ.get("DEADLINE_PATH", "")
    if env:
        if os.path.isfile(env):
            return env
        candidate = os.path.join(env, "deadlinecommand.exe")
        if os.path.isfile(candidate):
            return candidate
        candidate = os.path.join(env, "deadlinecommand")
        if os.path.isfile(candidate):
            return candidate

    for p in _DEFAULT_DEADLINE_PATHS:
        if os.path.isfile(p):
            return p

    raise FileNotFoundError(
        "Could not locate deadlinecommand. Set the DEADLINE_PATH environment "
        "variable to your Deadline bin directory."
    )


# ── Default job settings ─────────────────────────────────────────────────────
DEFAULT_PRIORITY = 50
DEFAULT_POOL = "nuke"
DEFAULT_GROUP = "nuke"
DEFAULT_CHUNK_SIZE = 10
DEFAULT_CONCURRENT_TASKS = 1
DEFAULT_NUKE_VERSION = "15.1"
DEFAULT_MACHINE_LIMIT = 0         # 0 = unlimited

# ── Nuke plugin name as registered in Deadline ────────────────────────────────
DEADLINE_NUKE_PLUGIN = "Nuke"
