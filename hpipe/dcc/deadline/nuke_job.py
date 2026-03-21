"""
Data model for a NukeX Deadline render job.

A :class:`NukeXJob` bundles everything needed to submit a single Write node
render to Deadline:

* The Nuke script path and Write node name.
* Frame range (from the script, the Write node, or explicit overrides).
* Deadline scheduling options (pool, group, priority, chunk size, …).
* Optional pipeline integration via :mod:`hpipe.assets.projectFile`.

Usage::

    from hpipe.dcc.deadline.nuke_job import NukeXJob

    job = NukeXJob(
        script_path=r"Y:/projects/2023/myshow/shots/SH010/working_files/nuke/SH010-comp-base-A01.nk",
        write_node="Write_comp",
    )
    # Override defaults
    job.priority = 75
    job.pool = "nuke_highpri"
    job.first_frame = 1001
    job.last_frame = 1050

    # Then hand to DeadlineSubmitter (see submission.py)
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
import os

from hpipe.core.hutils import logger
from hpipe.dcc.deadline import constants as dl_const
from hpipe.dcc.deadline.nuke_script import parse_nuke_script, NukeScriptInfo, WriteNodeInfo

log = logger.setup_logger()
log.debug("nuke_job.py loaded")


@dataclass
class NukeXJob:
    """
    Fully-specified NukeX render job ready for Deadline submission.

    Required fields:
        script_path: Absolute path to the .nk script.
        write_node:  Name of the Write (or DeepWrite) node to render.

    All other fields have sensible defaults drawn from
    :mod:`hpipe.dcc.deadline.constants` and can be overridden.
    """

    # ── Required ──────────────────────────────────────────────────────────
    script_path: str = ""
    write_node: str = ""

    # ── Frame range (None = use script/write-node range) ──────────────────
    first_frame: Optional[int] = None
    last_frame: Optional[int] = None
    frame_step: int = 1

    # ── Deadline scheduling ───────────────────────────────────────────────
    batch_name: str = ""
    job_name: str = ""
    comment: str = ""
    department: str = ""
    priority: int = dl_const.DEFAULT_PRIORITY
    pool: str = dl_const.DEFAULT_POOL
    secondary_pool: str = ""
    group: str = dl_const.DEFAULT_GROUP
    chunk_size: int = dl_const.DEFAULT_CHUNK_SIZE
    concurrent_tasks: int = dl_const.DEFAULT_CONCURRENT_TASKS
    machine_limit: int = dl_const.DEFAULT_MACHINE_LIMIT
    machine_list: str = ""
    machine_list_is_deny: bool = False

    # ── NukeX settings ────────────────────────────────────────────────────
    nuke_version: str = dl_const.DEFAULT_NUKE_VERSION
    use_nukex: bool = True
    use_gpu: bool = False
    render_threads: int = 0          # 0 = Nuke default
    memory_limit: int = 0            # MB, 0 = Nuke default
    continue_on_error: bool = True

    # ── Output tracking ──────────────────────────────────────────────────
    output_path: str = ""
    extra_info: Dict[str, str] = field(default_factory=dict)

    # ── Cached parse result (populated by validate()) ─────────────────────
    _script_info: Optional[NukeScriptInfo] = field(
        default=None, repr=False, compare=False
    )

    # ── Public API ────────────────────────────────────────────────────────

    def validate(self) -> List[str]:
        """
        Validate the job and return a list of error strings.
        An empty list means the job is ready to submit.

        Also populates default values (frame range, job name, output path)
        from the parsed script when they haven't been set explicitly.
        """
        errors: List[str] = []

        # Script exists?
        if not self.script_path:
            errors.append("script_path is required")
        elif not os.path.isfile(self.script_path):
            errors.append(f"Script file not found: {self.script_path}")

        if not self.write_node:
            errors.append("write_node name is required")

        if errors:
            return errors

        # Parse the script
        try:
            self._script_info = parse_nuke_script(self.script_path)
        except Exception as exc:
            errors.append(f"Failed to parse script: {exc}")
            return errors

        # Validate write node exists
        wn = self._script_info.get_write_node(self.write_node)
        if wn is None:
            available = ", ".join(self._script_info.get_write_node_names()) or "(none)"
            errors.append(
                f"Write node '{self.write_node}' not found in script. "
                f"Available: {available}"
            )
            return errors

        if wn.disable:
            errors.append(f"Write node '{self.write_node}' is disabled in the script.")

        # Populate defaults from script/write-node
        self._apply_defaults(wn)

        # Frame range sanity
        if self.first_frame is not None and self.last_frame is not None:
            if self.first_frame > self.last_frame:
                errors.append(
                    f"first_frame ({self.first_frame}) > last_frame ({self.last_frame})"
                )

        return errors

    def get_frame_string(self) -> str:
        """
        Return the Deadline-format frame string, e.g. ``1001-1100``,
        or ``1001-1100x2`` when frame_step > 1.
        """
        first = self.first_frame if self.first_frame is not None else 1001
        last = self.last_frame if self.last_frame is not None else 1100
        if self.frame_step > 1:
            return f"{first}-{last}x{self.frame_step}"
        return f"{first}-{last}"

    def build_job_info(self) -> Dict[str, str]:
        """
        Build the Deadline **Job Info** dictionary.
        These key-value pairs are written to the ``job_info.job`` file.
        """
        info: Dict[str, str] = {
            "Plugin": dl_const.DEADLINE_NUKE_PLUGIN,
            "Name": self.job_name,
            "Comment": self.comment,
            "Department": self.department,
            "BatchName": self.batch_name,
            "Priority": str(self.priority),
            "Pool": self.pool,
            "Group": self.group,
            "ChunkSize": str(self.chunk_size),
            "ConcurrentTasks": str(self.concurrent_tasks),
            "MachineLimit": str(self.machine_limit),
            "Frames": self.get_frame_string(),
        }

        if self.secondary_pool:
            info["SecondaryPool"] = self.secondary_pool

        if self.machine_list:
            if self.machine_list_is_deny:
                info["Denylist"] = self.machine_list
            else:
                info["Allowlist"] = self.machine_list

        if self.output_path:
            info["OutputDirectory0"] = os.path.dirname(self.output_path)
            info["OutputFilename0"] = os.path.basename(self.output_path)

        # Extra info key-value pairs (ExtraInfo0-9)
        for idx, (key, val) in enumerate(self.extra_info.items()):
            if idx > 9:
                break
            info[f"ExtraInfoKeyValue{idx}"] = f"{key}={val}"

        return info

    def build_plugin_info(self) -> Dict[str, str]:
        """
        Build the Deadline **Plugin Info** dictionary.
        These key-value pairs are written to the ``plugin_info.job`` file.
        """
        plugin: Dict[str, str] = {
            "SceneFile": self.script_path.replace("\\", "/"),
            "Version": self.nuke_version,
            "WriteNode": self.write_node,
            "NukeX": str(self.use_nukex),
            "UseGpu": str(self.use_gpu),
            "ContinueOnError": str(self.continue_on_error),
            "BatchMode": "True",
        }

        if self.render_threads > 0:
            plugin["Threads"] = str(self.render_threads)
        if self.memory_limit > 0:
            plugin["RamUse"] = str(self.memory_limit)

        return plugin

    # ── Internals ─────────────────────────────────────────────────────────

    def _apply_defaults(self, wn: WriteNodeInfo) -> None:
        """Fill in blanks from the parsed script / write node."""
        si = self._script_info
        assert si is not None

        # Frame range: explicit override > write-node limit > script root
        if self.first_frame is None:
            self.first_frame = wn.first_frame if wn.use_limit else si.first_frame
        if self.last_frame is None:
            self.last_frame = wn.last_frame if wn.use_limit else si.last_frame

        # Job name
        if not self.job_name:
            basename = os.path.splitext(os.path.basename(self.script_path))[0]
            self.job_name = f"{basename} — {self.write_node}"

        # Batch name
        if not self.batch_name:
            self.batch_name = os.path.splitext(os.path.basename(self.script_path))[0]

        # Output path
        if not self.output_path and wn.file_path:
            self.output_path = wn.file_path

        # Nuke version from script (if not overridden)
        if si.nuke_version and self.nuke_version == dl_const.DEFAULT_NUKE_VERSION:
            major_minor = ".".join(si.nuke_version.split(".")[:2])
            if major_minor:
                self.nuke_version = major_minor


@dataclass
class NukeXBatch:
    """
    Convenience wrapper for submitting multiple Write nodes from the same
    script as separate Deadline jobs that share a batch name.
    """
    script_path: str
    write_nodes: List[str] = field(default_factory=list)

    # Shared overrides (applied to every job)
    priority: int = dl_const.DEFAULT_PRIORITY
    pool: str = dl_const.DEFAULT_POOL
    group: str = dl_const.DEFAULT_GROUP
    chunk_size: int = dl_const.DEFAULT_CHUNK_SIZE
    first_frame: Optional[int] = None
    last_frame: Optional[int] = None
    nuke_version: str = dl_const.DEFAULT_NUKE_VERSION
    use_nukex: bool = True

    def build_jobs(self) -> List[NukeXJob]:
        """
        Create one :class:`NukeXJob` per write node.
        If *write_nodes* is empty, auto-discover all enabled Write nodes.
        """
        script_info = parse_nuke_script(self.script_path)
        batch_name = os.path.splitext(os.path.basename(self.script_path))[0]

        targets = self.write_nodes
        if not targets:
            targets = [wn.name for wn in script_info.get_enabled_write_nodes()]

        jobs: List[NukeXJob] = []
        for wn_name in targets:
            job = NukeXJob(
                script_path=self.script_path,
                write_node=wn_name,
                batch_name=batch_name,
                priority=self.priority,
                pool=self.pool,
                group=self.group,
                chunk_size=self.chunk_size,
                first_frame=self.first_frame,
                last_frame=self.last_frame,
                nuke_version=self.nuke_version,
                use_nukex=self.use_nukex,
            )
            jobs.append(job)

        return jobs
