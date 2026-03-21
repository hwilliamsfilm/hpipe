"""
Parse Nuke script (.nk) files to extract Write node names, output paths,
frame ranges, and file formats — without requiring a running Nuke session.

Nuke scripts are Tcl-like text files.  A Write node looks like::

    Write {
     file /path/to/output/shot_comp_v01_####.exr
     file_type exr
     name Write_comp
     ...
    }

This module uses simple regex/state-machine parsing rather than a full Tcl
parser, which is sufficient for the subset of syntax Nuke actually emits.
"""

import os
import re
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from hpipe.core.hutils import logger

log = logger.setup_logger()
log.debug("nuke_script.py loaded")


@dataclass
class WriteNodeInfo:
    """
    Data extracted from a single Write node in a .nk script.
    """
    name: str
    file_path: str = ""
    file_type: str = ""
    channels: str = "rgba"
    first_frame: Optional[int] = None
    last_frame: Optional[int] = None
    use_limit: bool = False
    disable: bool = False

    @property
    def is_enabled(self) -> bool:
        return not self.disable

    def output_directory(self) -> str:
        """Return the parent directory of the output file path."""
        return os.path.dirname(self.file_path)


@dataclass
class NukeScriptInfo:
    """
    Top-level data extracted from a .nk script.
    """
    script_path: str
    first_frame: int = 1001
    last_frame: int = 1100
    fps: float = 24.0
    nuke_version: str = ""
    write_nodes: List[WriteNodeInfo] = field(default_factory=list)

    def get_write_node(self, name: str) -> Optional[WriteNodeInfo]:
        """Return the WriteNodeInfo with the given *name*, or None."""
        for wn in self.write_nodes:
            if wn.name == name:
                return wn
        return None

    def get_write_node_names(self) -> List[str]:
        """Return all Write node names in the script."""
        return [wn.name for wn in self.write_nodes]

    def get_enabled_write_nodes(self) -> List[WriteNodeInfo]:
        """Return only non-disabled Write nodes."""
        return [wn for wn in self.write_nodes if wn.is_enabled]


# ── Regex helpers ─────────────────────────────────────────────────────────────

_RE_NODE_START = re.compile(r"^(\w+)\s*\{")
_RE_KNOB_VALUE = re.compile(r"^\s+(\w+)\s+(.*)")
_RE_ROOT_FORMAT_FRAMES = re.compile(r"first_frame\s+(\d+)")


def _strip_quotes(value: str) -> str:
    """Remove surrounding double-quotes if present."""
    if value.startswith('"') and value.endswith('"'):
        return value[1:-1]
    return value


# ── Main parser ──────────────────────────────────────────────────────────────

def parse_nuke_script(script_path: str) -> NukeScriptInfo:
    """
    Parse a ``.nk`` file and return a :class:`NukeScriptInfo` with all Write
    nodes and global frame-range settings.

    :param script_path: Absolute path to the Nuke script.
    :raises FileNotFoundError: If *script_path* does not exist.
    :raises ValueError: If the file cannot be read or has no recognisable content.
    """
    if not os.path.isfile(script_path):
        raise FileNotFoundError(f"Nuke script not found: {script_path}")

    with open(script_path, "r", encoding="utf-8", errors="replace") as fh:
        lines = fh.readlines()

    info = NukeScriptInfo(script_path=script_path)

    current_node_type: Optional[str] = None
    current_knobs: dict = {}
    brace_depth = 0

    _RE_TOP_LEVEL_VERSION = re.compile(r"^version\s+([\d.]+)")

    for line in lines:
        stripped = line.rstrip("\n\r")

        # ── Top-level "version X.Y vN" header (outside any node) ─────────
        if brace_depth == 0:
            vm = _RE_TOP_LEVEL_VERSION.match(stripped)
            if vm:
                info.nuke_version = vm.group(1)

        # ── Detect node open ──────────────────────────────────────────────
        m = _RE_NODE_START.match(stripped)
        if m and brace_depth == 0:
            current_node_type = m.group(1)
            current_knobs = {}
            brace_depth = 1
            continue

        # ── Track brace depth ─────────────────────────────────────────────
        if brace_depth > 0:
            brace_depth += stripped.count("{") - stripped.count("}")

            # Collect knob values
            km = _RE_KNOB_VALUE.match(stripped)
            if km:
                current_knobs[km.group(1)] = _strip_quotes(km.group(2).strip())

            # ── Node close ────────────────────────────────────────────────
            if brace_depth <= 0:
                brace_depth = 0
                if current_node_type == "Root":
                    _parse_root_knobs(info, current_knobs)
                elif current_node_type in ("Write", "DeepWrite"):
                    _parse_write_knobs(info, current_knobs)
                current_node_type = None
            continue

    log.debug(
        f"Parsed {script_path}: frames {info.first_frame}-{info.last_frame}, "
        f"{len(info.write_nodes)} Write node(s)"
    )
    return info


def _parse_root_knobs(info: NukeScriptInfo, knobs: dict) -> None:
    """Extract global settings from the Root node knobs."""
    if "first_frame" in knobs:
        try:
            info.first_frame = int(float(knobs["first_frame"]))
        except ValueError:
            pass
    if "last_frame" in knobs:
        try:
            info.last_frame = int(float(knobs["last_frame"]))
        except ValueError:
            pass
    if "fps" in knobs:
        try:
            info.fps = float(knobs["fps"])
        except ValueError:
            pass
    if "version" in knobs:
        info.nuke_version = knobs["version"]


def _parse_write_knobs(info: NukeScriptInfo, knobs: dict) -> None:
    """Build a :class:`WriteNodeInfo` from collected knobs and append it."""
    name = knobs.get("name", f"Write_{len(info.write_nodes) + 1}")

    wn = WriteNodeInfo(
        name=name,
        file_path=knobs.get("file", ""),
        file_type=knobs.get("file_type", ""),
        channels=knobs.get("channels", "rgba"),
        disable=knobs.get("disable", "false").lower() == "true",
    )

    # Per-node frame range (use_limit knob)
    if knobs.get("use_limit", "false").lower() == "true":
        wn.use_limit = True
        try:
            wn.first_frame = int(float(knobs.get("first", info.first_frame)))
        except (ValueError, TypeError):
            wn.first_frame = info.first_frame
        try:
            wn.last_frame = int(float(knobs.get("last", info.last_frame)))
        except (ValueError, TypeError):
            wn.last_frame = info.last_frame

    info.write_nodes.append(wn)
