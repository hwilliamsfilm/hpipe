"""
Submit NukeX render jobs to Deadline.

This module writes Deadline info files to a temp directory and invokes
``deadlinecommand`` to submit them.  It does *not* require a running Nuke or
Deadline Monitor session — only the Deadline Client CLI.

Usage::

    from hpipe.dcc.deadline.nuke_job import NukeXJob
    from hpipe.dcc.deadline.submission import DeadlineSubmitter

    job = NukeXJob(
        script_path=r"Y:/projects/2023/show/shots/SH010/.../comp.nk",
        write_node="Write_comp",
    )

    submitter = DeadlineSubmitter()
    result = submitter.submit(job)
    print(result.job_id, result.message)
"""

import os
import subprocess
import tempfile
from dataclasses import dataclass, field
from typing import List, Optional

from hpipe.core.hutils import logger
from hpipe.dcc.deadline import constants as dl_const
from hpipe.dcc.deadline.nuke_job import NukeXJob, NukeXBatch

log = logger.setup_logger()
log.debug("submission.py loaded")


@dataclass
class SubmissionResult:
    """Result of a single Deadline job submission."""
    success: bool
    job_id: str = ""
    message: str = ""
    raw_output: str = ""


def _write_info_file(path: str, data: dict) -> None:
    """Write a Deadline key=value info file."""
    with open(path, "w", encoding="utf-8") as fh:
        for key, value in data.items():
            fh.write(f"{key}={value}\n")


class DeadlineSubmitter:
    """
    Submits :class:`NukeXJob` instances to Deadline via the CLI.

    :param deadline_command: Override the path to ``deadlinecommand``.
        If *None*, it is resolved via :func:`constants.get_deadline_command`.
    :param dry_run: If *True*, build the info files and log the command but
        do not actually invoke ``deadlinecommand``.  Useful for testing.
    """

    def __init__(self, deadline_command: Optional[str] = None, dry_run: bool = False):
        self._dry_run = dry_run
        if deadline_command:
            self._cmd = deadline_command
        elif dry_run:
            self._cmd = "deadlinecommand"
        else:
            self._cmd = dl_const.get_deadline_command()

    # ── Public API ────────────────────────────────────────────────────────

    def submit(self, job: NukeXJob) -> SubmissionResult:
        """
        Validate and submit a single NukeX job to Deadline.

        :param job: A fully configured :class:`NukeXJob`.
        :returns: :class:`SubmissionResult` with *success*, *job_id*, and
            the raw Deadline output.
        """
        errors = job.validate()
        if errors:
            msg = "; ".join(errors)
            log.error(f"Job validation failed: {msg}")
            return SubmissionResult(success=False, message=msg)

        job_info = job.build_job_info()
        plugin_info = job.build_plugin_info()

        return self._submit_info_files(job_info, plugin_info)

    def submit_batch(self, batch: NukeXBatch) -> List[SubmissionResult]:
        """
        Submit all jobs in a :class:`NukeXBatch`.

        :returns: One :class:`SubmissionResult` per Write node.
        """
        jobs = batch.build_jobs()
        results: List[SubmissionResult] = []
        for job in jobs:
            results.append(self.submit(job))
        return results

    # ── Internals ─────────────────────────────────────────────────────────

    def _submit_info_files(self, job_info: dict, plugin_info: dict) -> SubmissionResult:
        """Write temp info files and invoke deadlinecommand."""
        tmp_dir = tempfile.mkdtemp(prefix="hpipe_deadline_")
        job_info_path = os.path.join(tmp_dir, "job_info.job")
        plugin_info_path = os.path.join(tmp_dir, "plugin_info.job")

        _write_info_file(job_info_path, job_info)
        _write_info_file(plugin_info_path, plugin_info)

        log.info(f"Job info written to {job_info_path}")
        log.info(f"Plugin info written to {plugin_info_path}")
        log.debug(f"Job info: {job_info}")
        log.debug(f"Plugin info: {plugin_info}")

        cmd = [self._cmd, job_info_path, plugin_info_path]

        if self._dry_run:
            log.info(f"[DRY RUN] Would execute: {' '.join(cmd)}")
            return SubmissionResult(
                success=True,
                job_id="dry-run-00000000",
                message="Dry run — no job submitted.",
                raw_output="",
            )

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,
            )
        except FileNotFoundError:
            msg = f"deadlinecommand not found at: {self._cmd}"
            log.error(msg)
            return SubmissionResult(success=False, message=msg)
        except subprocess.TimeoutExpired:
            msg = "deadlinecommand timed out after 120 seconds."
            log.error(msg)
            return SubmissionResult(success=False, message=msg)

        raw = result.stdout.strip()
        log.debug(f"deadlinecommand stdout: {raw}")
        if result.stderr.strip():
            log.debug(f"deadlinecommand stderr: {result.stderr.strip()}")

        if result.returncode != 0:
            return SubmissionResult(
                success=False,
                message=f"deadlinecommand exited with code {result.returncode}",
                raw_output=raw,
            )

        job_id = _extract_job_id(raw)
        return SubmissionResult(
            success=True,
            job_id=job_id,
            message="Job submitted successfully.",
            raw_output=raw,
        )


def _extract_job_id(output: str) -> str:
    """
    Pull the Deadline Job ID out of the ``deadlinecommand`` stdout.

    Deadline typically prints::

        JobID=<hex-string>

    or a line containing the 24-character hex ID.
    """
    for line in output.splitlines():
        if "JobID=" in line:
            return line.split("JobID=")[-1].strip()
        # Fallback: look for a 24-char hex string (Deadline standard)
        stripped = line.strip()
        if len(stripped) == 24 and all(c in "0123456789abcdef" for c in stripped):
            return stripped
    return ""


# ── Convenience function ──────────────────────────────────────────────────────

def submit_nuke_job(
    script_path: str,
    write_node: str,
    first_frame: Optional[int] = None,
    last_frame: Optional[int] = None,
    priority: int = dl_const.DEFAULT_PRIORITY,
    pool: str = dl_const.DEFAULT_POOL,
    group: str = dl_const.DEFAULT_GROUP,
    chunk_size: int = dl_const.DEFAULT_CHUNK_SIZE,
    nuke_version: str = dl_const.DEFAULT_NUKE_VERSION,
    use_nukex: bool = True,
    dry_run: bool = False,
) -> SubmissionResult:
    """
    One-call convenience function: build a job and submit it.

    ::

        from hpipe.dcc.deadline.submission import submit_nuke_job

        result = submit_nuke_job(
            script_path="/path/to/comp.nk",
            write_node="Write_comp",
            first_frame=1001,
            last_frame=1050,
        )
    """
    job = NukeXJob(
        script_path=script_path,
        write_node=write_node,
        first_frame=first_frame,
        last_frame=last_frame,
        priority=priority,
        pool=pool,
        group=group,
        chunk_size=chunk_size,
        nuke_version=nuke_version,
        use_nukex=use_nukex,
    )
    submitter = DeadlineSubmitter(dry_run=dry_run)
    return submitter.submit(job)
