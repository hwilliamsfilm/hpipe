"""
Tests for hpipe.dcc.deadline — NukeX Deadline submission package.

Covers:
    - Nuke script parsing (nuke_script.py)
    - Job construction and validation (nuke_job.py)
    - Info-file generation (nuke_job.py build_job_info / build_plugin_info)
    - Batch job creation (nuke_job.py NukeXBatch)
    - Submission dry-run (submission.py DeadlineSubmitter)
    - Convenience function (submission.py submit_nuke_job)
    - Edge cases: missing files, bad write nodes, disabled nodes, etc.

All tests are offline — no Nuke session or Deadline installation required.
"""

import os
import textwrap
import tempfile
import pytest
from unittest.mock import patch, MagicMock

# ── Fixtures ──────────────────────────────────────────────────────────────────

SAMPLE_NK_SCRIPT = textwrap.dedent("""\
    #! /opt/Nuke15.1v1/libnuke-15.1.1.so -nx
    version 15.1 v1
    Root {
     inputs 0
     name /projects/2023/myshow/shots/SH010/working_files/nuke/SH010-comp-base-A01.nk
     first_frame 1001
     last_frame 1100
     fps 24
    }
    Read {
     inputs 0
     file /projects/2023/myshow/shots/SH010/plate/main/SH010_plate_####.exr
     name Read_plate
    }
    Write {
     file /projects/2023/myshow/shots/SH010/output/comp/main/exr/SH010-comp-base-A01_####.exr
     file_type exr
     channels rgba
     name Write_comp
    }
    Write {
     file /projects/2023/myshow/shots/SH010/output/comp/main/jpg/SH010-comp-base-A01_####.jpg
     file_type jpeg
     channels rgb
     name Write_jpg
    }
    Write {
     file /projects/2023/myshow/shots/SH010/output/_workarea/denoise/SH010_denoise_####.exr
     file_type exr
     name Write_denoise
     use_limit true
     first 1010
     last 1050
    }
    Write {
     file /projects/2023/myshow/shots/SH010/output/comp/disabled/SH010_disabled_####.exr
     file_type exr
     name Write_disabled
     disable true
    }
""")


@pytest.fixture
def nk_script_path(tmp_path):
    """Write the sample .nk content to a temp file and return the path."""
    nk_file = tmp_path / "SH010-comp-base-A01.nk"
    nk_file.write_text(SAMPLE_NK_SCRIPT, encoding="utf-8")
    return str(nk_file)


# =============================================================================
# nuke_script.py — Parsing
# =============================================================================

class TestNukeScriptParser:

    def test_parse_root_frame_range(self, nk_script_path):
        from hpipe.dcc.deadline.nuke_script import parse_nuke_script
        info = parse_nuke_script(nk_script_path)
        assert info.first_frame == 1001
        assert info.last_frame == 1100

    def test_parse_root_fps(self, nk_script_path):
        from hpipe.dcc.deadline.nuke_script import parse_nuke_script
        info = parse_nuke_script(nk_script_path)
        assert info.fps == 24.0

    def test_parse_root_nuke_version(self, nk_script_path):
        from hpipe.dcc.deadline.nuke_script import parse_nuke_script
        info = parse_nuke_script(nk_script_path)
        assert "15.1" in info.nuke_version

    def test_parse_finds_all_write_nodes(self, nk_script_path):
        from hpipe.dcc.deadline.nuke_script import parse_nuke_script
        info = parse_nuke_script(nk_script_path)
        assert len(info.write_nodes) == 4

    def test_parse_write_node_names(self, nk_script_path):
        from hpipe.dcc.deadline.nuke_script import parse_nuke_script
        info = parse_nuke_script(nk_script_path)
        names = info.get_write_node_names()
        assert "Write_comp" in names
        assert "Write_jpg" in names
        assert "Write_denoise" in names
        assert "Write_disabled" in names

    def test_parse_write_node_file_path(self, nk_script_path):
        from hpipe.dcc.deadline.nuke_script import parse_nuke_script
        info = parse_nuke_script(nk_script_path)
        wn = info.get_write_node("Write_comp")
        assert wn is not None
        assert "SH010-comp-base-A01_####.exr" in wn.file_path

    def test_parse_write_node_file_type(self, nk_script_path):
        from hpipe.dcc.deadline.nuke_script import parse_nuke_script
        info = parse_nuke_script(nk_script_path)
        wn = info.get_write_node("Write_comp")
        assert wn.file_type == "exr"

    def test_parse_write_node_channels(self, nk_script_path):
        from hpipe.dcc.deadline.nuke_script import parse_nuke_script
        info = parse_nuke_script(nk_script_path)
        assert info.get_write_node("Write_comp").channels == "rgba"
        assert info.get_write_node("Write_jpg").channels == "rgb"

    def test_parse_write_node_use_limit(self, nk_script_path):
        from hpipe.dcc.deadline.nuke_script import parse_nuke_script
        info = parse_nuke_script(nk_script_path)
        wn = info.get_write_node("Write_denoise")
        assert wn.use_limit is True
        assert wn.first_frame == 1010
        assert wn.last_frame == 1050

    def test_parse_write_node_disabled(self, nk_script_path):
        from hpipe.dcc.deadline.nuke_script import parse_nuke_script
        info = parse_nuke_script(nk_script_path)
        wn = info.get_write_node("Write_disabled")
        assert wn.disable is True
        assert wn.is_enabled is False

    def test_enabled_write_nodes_excludes_disabled(self, nk_script_path):
        from hpipe.dcc.deadline.nuke_script import parse_nuke_script
        info = parse_nuke_script(nk_script_path)
        enabled = info.get_enabled_write_nodes()
        names = [wn.name for wn in enabled]
        assert "Write_disabled" not in names
        assert len(enabled) == 3

    def test_get_write_node_returns_none_for_missing(self, nk_script_path):
        from hpipe.dcc.deadline.nuke_script import parse_nuke_script
        info = parse_nuke_script(nk_script_path)
        assert info.get_write_node("Nonexistent") is None

    def test_parse_nonexistent_file_raises(self):
        from hpipe.dcc.deadline.nuke_script import parse_nuke_script
        with pytest.raises(FileNotFoundError):
            parse_nuke_script("/no/such/file.nk")

    def test_output_directory(self, nk_script_path):
        from hpipe.dcc.deadline.nuke_script import parse_nuke_script
        info = parse_nuke_script(nk_script_path)
        wn = info.get_write_node("Write_comp")
        assert wn.output_directory().endswith("exr")

    def test_parse_empty_script(self, tmp_path):
        from hpipe.dcc.deadline.nuke_script import parse_nuke_script
        empty = tmp_path / "empty.nk"
        empty.write_text("", encoding="utf-8")
        info = parse_nuke_script(str(empty))
        assert len(info.write_nodes) == 0
        # defaults
        assert info.first_frame == 1001
        assert info.last_frame == 1100


# =============================================================================
# nuke_job.py — Job construction
# =============================================================================

class TestNukeXJob:

    def test_validate_succeeds(self, nk_script_path):
        from hpipe.dcc.deadline.nuke_job import NukeXJob
        job = NukeXJob(script_path=nk_script_path, write_node="Write_comp")
        errors = job.validate()
        assert errors == [], f"Unexpected errors: {errors}"

    def test_validate_populates_frame_range_from_script(self, nk_script_path):
        from hpipe.dcc.deadline.nuke_job import NukeXJob
        job = NukeXJob(script_path=nk_script_path, write_node="Write_comp")
        job.validate()
        assert job.first_frame == 1001
        assert job.last_frame == 1100

    def test_validate_uses_write_node_limit(self, nk_script_path):
        from hpipe.dcc.deadline.nuke_job import NukeXJob
        job = NukeXJob(script_path=nk_script_path, write_node="Write_denoise")
        job.validate()
        assert job.first_frame == 1010
        assert job.last_frame == 1050

    def test_validate_explicit_frame_override(self, nk_script_path):
        from hpipe.dcc.deadline.nuke_job import NukeXJob
        job = NukeXJob(
            script_path=nk_script_path,
            write_node="Write_comp",
            first_frame=900,
            last_frame=950,
        )
        job.validate()
        assert job.first_frame == 900
        assert job.last_frame == 950

    def test_validate_generates_job_name(self, nk_script_path):
        from hpipe.dcc.deadline.nuke_job import NukeXJob
        job = NukeXJob(script_path=nk_script_path, write_node="Write_comp")
        job.validate()
        assert "Write_comp" in job.job_name
        assert "SH010" in job.job_name

    def test_validate_generates_batch_name(self, nk_script_path):
        from hpipe.dcc.deadline.nuke_job import NukeXJob
        job = NukeXJob(script_path=nk_script_path, write_node="Write_comp")
        job.validate()
        assert job.batch_name != ""

    def test_validate_populates_output_path(self, nk_script_path):
        from hpipe.dcc.deadline.nuke_job import NukeXJob
        job = NukeXJob(script_path=nk_script_path, write_node="Write_comp")
        job.validate()
        assert "SH010-comp-base-A01_####.exr" in job.output_path

    def test_validate_detects_nuke_version(self, nk_script_path):
        from hpipe.dcc.deadline.nuke_job import NukeXJob
        job = NukeXJob(script_path=nk_script_path, write_node="Write_comp")
        job.validate()
        assert job.nuke_version == "15.1"

    def test_validate_missing_script(self):
        from hpipe.dcc.deadline.nuke_job import NukeXJob
        job = NukeXJob(script_path="/no/file.nk", write_node="Write1")
        errors = job.validate()
        assert len(errors) > 0
        assert "not found" in errors[0].lower()

    def test_validate_empty_script_path(self):
        from hpipe.dcc.deadline.nuke_job import NukeXJob
        job = NukeXJob(script_path="", write_node="Write1")
        errors = job.validate()
        assert any("required" in e.lower() for e in errors)

    def test_validate_empty_write_node(self, nk_script_path):
        from hpipe.dcc.deadline.nuke_job import NukeXJob
        job = NukeXJob(script_path=nk_script_path, write_node="")
        errors = job.validate()
        assert any("required" in e.lower() for e in errors)

    def test_validate_wrong_write_node(self, nk_script_path):
        from hpipe.dcc.deadline.nuke_job import NukeXJob
        job = NukeXJob(script_path=nk_script_path, write_node="DoesNotExist")
        errors = job.validate()
        assert any("not found" in e.lower() for e in errors)
        assert "Write_comp" in errors[0]  # should list available nodes

    def test_validate_disabled_write_node(self, nk_script_path):
        from hpipe.dcc.deadline.nuke_job import NukeXJob
        job = NukeXJob(script_path=nk_script_path, write_node="Write_disabled")
        errors = job.validate()
        assert any("disabled" in e.lower() for e in errors)

    def test_validate_bad_frame_range(self, nk_script_path):
        from hpipe.dcc.deadline.nuke_job import NukeXJob
        job = NukeXJob(
            script_path=nk_script_path,
            write_node="Write_comp",
            first_frame=1100,
            last_frame=1000,
        )
        errors = job.validate()
        assert any("first_frame" in e for e in errors)

    def test_get_frame_string(self, nk_script_path):
        from hpipe.dcc.deadline.nuke_job import NukeXJob
        job = NukeXJob(
            script_path=nk_script_path,
            write_node="Write_comp",
            first_frame=1001,
            last_frame=1100,
        )
        assert job.get_frame_string() == "1001-1100"

    def test_get_frame_string_with_step(self, nk_script_path):
        from hpipe.dcc.deadline.nuke_job import NukeXJob
        job = NukeXJob(
            script_path=nk_script_path,
            write_node="Write_comp",
            first_frame=1001,
            last_frame=1100,
            frame_step=2,
        )
        assert job.get_frame_string() == "1001-1100x2"


# =============================================================================
# nuke_job.py — Info file generation
# =============================================================================

class TestNukeXJobInfoFiles:

    def test_build_job_info_has_required_keys(self, nk_script_path):
        from hpipe.dcc.deadline.nuke_job import NukeXJob
        job = NukeXJob(script_path=nk_script_path, write_node="Write_comp")
        job.validate()
        info = job.build_job_info()
        assert info["Plugin"] == "Nuke"
        assert "Write_comp" in info["Name"]
        assert info["Frames"] == "1001-1100"
        assert "Priority" in info
        assert "Pool" in info
        assert "ChunkSize" in info

    def test_build_plugin_info_has_required_keys(self, nk_script_path):
        from hpipe.dcc.deadline.nuke_job import NukeXJob
        job = NukeXJob(script_path=nk_script_path, write_node="Write_comp")
        job.validate()
        plugin = job.build_plugin_info()
        assert plugin["WriteNode"] == "Write_comp"
        assert plugin["NukeX"] == "True"
        assert plugin["Version"] == "15.1"
        assert nk_script_path.replace("\\", "/") in plugin["SceneFile"]

    def test_build_job_info_output_path(self, nk_script_path):
        from hpipe.dcc.deadline.nuke_job import NukeXJob
        job = NukeXJob(script_path=nk_script_path, write_node="Write_comp")
        job.validate()
        info = job.build_job_info()
        assert "OutputDirectory0" in info
        assert "OutputFilename0" in info

    def test_build_job_info_custom_priority(self, nk_script_path):
        from hpipe.dcc.deadline.nuke_job import NukeXJob
        job = NukeXJob(
            script_path=nk_script_path,
            write_node="Write_comp",
            priority=90,
        )
        job.validate()
        info = job.build_job_info()
        assert info["Priority"] == "90"

    def test_build_plugin_info_gpu_and_threads(self, nk_script_path):
        from hpipe.dcc.deadline.nuke_job import NukeXJob
        job = NukeXJob(
            script_path=nk_script_path,
            write_node="Write_comp",
            use_gpu=True,
            render_threads=8,
            memory_limit=4096,
        )
        job.validate()
        plugin = job.build_plugin_info()
        assert plugin["UseGpu"] == "True"
        assert plugin["Threads"] == "8"
        assert plugin["RamUse"] == "4096"

    def test_build_job_info_machine_list(self, nk_script_path):
        from hpipe.dcc.deadline.nuke_job import NukeXJob
        job = NukeXJob(
            script_path=nk_script_path,
            write_node="Write_comp",
            machine_list="render01,render02",
            machine_list_is_deny=False,
        )
        job.validate()
        info = job.build_job_info()
        assert info["Allowlist"] == "render01,render02"

    def test_build_job_info_deny_list(self, nk_script_path):
        from hpipe.dcc.deadline.nuke_job import NukeXJob
        job = NukeXJob(
            script_path=nk_script_path,
            write_node="Write_comp",
            machine_list="render03",
            machine_list_is_deny=True,
        )
        job.validate()
        info = job.build_job_info()
        assert info["Denylist"] == "render03"
        assert "Allowlist" not in info


# =============================================================================
# nuke_job.py — Batch
# =============================================================================

class TestNukeXBatch:

    def test_batch_builds_jobs_for_all_enabled(self, nk_script_path):
        from hpipe.dcc.deadline.nuke_job import NukeXBatch
        batch = NukeXBatch(script_path=nk_script_path)
        jobs = batch.build_jobs()
        # 3 enabled write nodes (Write_disabled is excluded)
        assert len(jobs) == 3
        names = [j.write_node for j in jobs]
        assert "Write_comp" in names
        assert "Write_jpg" in names
        assert "Write_denoise" in names
        assert "Write_disabled" not in names

    def test_batch_explicit_write_nodes(self, nk_script_path):
        from hpipe.dcc.deadline.nuke_job import NukeXBatch
        batch = NukeXBatch(
            script_path=nk_script_path,
            write_nodes=["Write_comp"],
        )
        jobs = batch.build_jobs()
        assert len(jobs) == 1
        assert jobs[0].write_node == "Write_comp"

    def test_batch_shares_settings(self, nk_script_path):
        from hpipe.dcc.deadline.nuke_job import NukeXBatch
        batch = NukeXBatch(
            script_path=nk_script_path,
            priority=85,
            pool="nuke_highpri",
            chunk_size=5,
        )
        jobs = batch.build_jobs()
        for job in jobs:
            assert job.priority == 85
            assert job.pool == "nuke_highpri"
            assert job.chunk_size == 5

    def test_batch_frame_override(self, nk_script_path):
        from hpipe.dcc.deadline.nuke_job import NukeXBatch
        batch = NukeXBatch(
            script_path=nk_script_path,
            first_frame=1001,
            last_frame=1010,
        )
        jobs = batch.build_jobs()
        for job in jobs:
            assert job.first_frame == 1001
            assert job.last_frame == 1010


# =============================================================================
# submission.py — DeadlineSubmitter
# =============================================================================

class TestDeadlineSubmitter:

    def test_dry_run_succeeds(self, nk_script_path):
        from hpipe.dcc.deadline.submission import DeadlineSubmitter
        from hpipe.dcc.deadline.nuke_job import NukeXJob

        job = NukeXJob(script_path=nk_script_path, write_node="Write_comp")
        submitter = DeadlineSubmitter(dry_run=True)
        result = submitter.submit(job)
        assert result.success is True
        assert result.job_id == "dry-run-00000000"

    def test_validation_failure_returns_error(self):
        from hpipe.dcc.deadline.submission import DeadlineSubmitter
        from hpipe.dcc.deadline.nuke_job import NukeXJob

        job = NukeXJob(script_path="/no/file.nk", write_node="Write1")
        submitter = DeadlineSubmitter(dry_run=True)
        result = submitter.submit(job)
        assert result.success is False
        assert result.message != ""

    def test_wrong_write_node_returns_error(self, nk_script_path):
        from hpipe.dcc.deadline.submission import DeadlineSubmitter
        from hpipe.dcc.deadline.nuke_job import NukeXJob

        job = NukeXJob(script_path=nk_script_path, write_node="Bogus")
        submitter = DeadlineSubmitter(dry_run=True)
        result = submitter.submit(job)
        assert result.success is False
        assert "not found" in result.message.lower()

    def test_submit_writes_info_files(self, nk_script_path):
        """Verify that info files are actually written to disk in dry-run."""
        from hpipe.dcc.deadline.submission import DeadlineSubmitter, _write_info_file
        from hpipe.dcc.deadline.nuke_job import NukeXJob
        import tempfile

        job = NukeXJob(script_path=nk_script_path, write_node="Write_comp")
        job.validate()

        tmp = tempfile.mkdtemp()
        job_path = os.path.join(tmp, "job_info.job")
        plugin_path = os.path.join(tmp, "plugin_info.job")

        _write_info_file(job_path, job.build_job_info())
        _write_info_file(plugin_path, job.build_plugin_info())

        assert os.path.isfile(job_path)
        assert os.path.isfile(plugin_path)

        with open(job_path) as fh:
            content = fh.read()
        assert "Plugin=Nuke" in content
        assert "Write_comp" in content

    def test_submit_batch_dry_run(self, nk_script_path):
        from hpipe.dcc.deadline.submission import DeadlineSubmitter
        from hpipe.dcc.deadline.nuke_job import NukeXBatch

        batch = NukeXBatch(script_path=nk_script_path)
        submitter = DeadlineSubmitter(dry_run=True)
        results = submitter.submit_batch(batch)
        assert len(results) == 3
        assert all(r.success for r in results)

    def test_submit_handles_missing_deadline_command(self, nk_script_path):
        """When not in dry-run and deadlinecommand is missing, return error."""
        from hpipe.dcc.deadline.submission import DeadlineSubmitter
        from hpipe.dcc.deadline.nuke_job import NukeXJob

        job = NukeXJob(script_path=nk_script_path, write_node="Write_comp")
        submitter = DeadlineSubmitter(
            deadline_command="/nonexistent/deadlinecommand",
            dry_run=False,
        )
        result = submitter.submit(job)
        assert result.success is False
        assert "not found" in result.message.lower()


# =============================================================================
# submission.py — Convenience function
# =============================================================================

class TestSubmitNukeJobConvenience:

    def test_submit_nuke_job_dry_run(self, nk_script_path):
        from hpipe.dcc.deadline.submission import submit_nuke_job
        result = submit_nuke_job(
            script_path=nk_script_path,
            write_node="Write_comp",
            dry_run=True,
        )
        assert result.success is True

    def test_submit_nuke_job_with_overrides(self, nk_script_path):
        from hpipe.dcc.deadline.submission import submit_nuke_job
        result = submit_nuke_job(
            script_path=nk_script_path,
            write_node="Write_comp",
            first_frame=1001,
            last_frame=1010,
            priority=80,
            pool="nuke_urgent",
            chunk_size=5,
            dry_run=True,
        )
        assert result.success is True

    def test_submit_nuke_job_invalid_write_node(self, nk_script_path):
        from hpipe.dcc.deadline.submission import submit_nuke_job
        result = submit_nuke_job(
            script_path=nk_script_path,
            write_node="NoSuchNode",
            dry_run=True,
        )
        assert result.success is False


# =============================================================================
# Constants
# =============================================================================

class TestConstants:

    def test_default_values_exist(self):
        from hpipe.dcc.deadline import constants as c
        assert c.DEFAULT_PRIORITY == 50
        assert isinstance(c.DEFAULT_POOL, str)
        assert isinstance(c.DEFAULT_GROUP, str)
        assert c.DEFAULT_CHUNK_SIZE > 0

    def test_get_deadline_command_raises_when_missing(self):
        from hpipe.dcc.deadline import constants as c
        with patch.dict(os.environ, {}, clear=True):
            with patch("os.path.isfile", return_value=False):
                with pytest.raises(FileNotFoundError):
                    c.get_deadline_command()

    def test_get_deadline_command_from_env(self, tmp_path):
        from hpipe.dcc.deadline import constants as c
        fake_exe = tmp_path / "deadlinecommand.exe"
        fake_exe.write_text("fake")
        with patch.dict(os.environ, {"DEADLINE_PATH": str(tmp_path)}):
            result = c.get_deadline_command()
        assert "deadlinecommand" in result


# =============================================================================
# Edge cases
# =============================================================================

class TestEdgeCases:

    def test_script_with_only_root_no_writes(self, tmp_path):
        """A script with a Root but no Write nodes should parse cleanly."""
        from hpipe.dcc.deadline.nuke_script import parse_nuke_script
        nk = tmp_path / "no_writes.nk"
        nk.write_text(textwrap.dedent("""\
            Root {
             first_frame 1
             last_frame 100
            }
        """))
        info = parse_nuke_script(str(nk))
        assert info.first_frame == 1
        assert info.last_frame == 100
        assert len(info.write_nodes) == 0

    def test_write_node_with_no_file_knob(self, tmp_path):
        """A Write node without a file path should still parse."""
        from hpipe.dcc.deadline.nuke_script import parse_nuke_script
        nk = tmp_path / "no_file.nk"
        nk.write_text(textwrap.dedent("""\
            Root {
             first_frame 1001
             last_frame 1100
            }
            Write {
             name Write_empty
            }
        """))
        info = parse_nuke_script(str(nk))
        assert len(info.write_nodes) == 1
        assert info.write_nodes[0].file_path == ""

    def test_nested_braces_in_knob_expressions(self, tmp_path):
        """Knob values with curly braces (expressions) should not break parsing."""
        from hpipe.dcc.deadline.nuke_script import parse_nuke_script
        nk = tmp_path / "expressions.nk"
        nk.write_text(textwrap.dedent("""\
            Root {
             first_frame 1001
             last_frame 1100
            }
            Write {
             file /path/to/output_####.exr
             file_type exr
             name Write_expr
            }
        """))
        info = parse_nuke_script(str(nk))
        assert len(info.write_nodes) == 1
        assert info.write_nodes[0].name == "Write_expr"

    def test_quoted_file_path(self, tmp_path):
        """File paths with quotes should have quotes stripped."""
        from hpipe.dcc.deadline.nuke_script import parse_nuke_script
        nk = tmp_path / "quoted.nk"
        nk.write_text(textwrap.dedent("""\
            Root {
             first_frame 1001
             last_frame 1100
            }
            Write {
             file "/path/with spaces/output_####.exr"
             file_type exr
             name Write_quoted
            }
        """))
        info = parse_nuke_script(str(nk))
        wn = info.get_write_node("Write_quoted")
        assert wn is not None
        assert not wn.file_path.startswith('"')
        assert "with spaces" in wn.file_path

    def test_job_extra_info(self, nk_script_path):
        """Extra info key-value pairs should appear in job info."""
        from hpipe.dcc.deadline.nuke_job import NukeXJob
        job = NukeXJob(
            script_path=nk_script_path,
            write_node="Write_comp",
            extra_info={"project": "myshow", "shot": "SH010"},
        )
        job.validate()
        info = job.build_job_info()
        extra_vals = [v for k, v in info.items() if k.startswith("ExtraInfoKeyValue")]
        assert any("myshow" in v for v in extra_vals)
        assert any("SH010" in v for v in extra_vals)
