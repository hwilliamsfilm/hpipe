"""
Tests for the Output Viewer's reviewable pipeline.

These tests diagnose why only Comps show up in the GUI while Renders, Plates,
Project Files, Workarea, and Ref types return nothing.

Run with:
    python -m pytest hpipe/tests/test_output_reviewables.py -v
"""

import os
import pytest
from unittest.mock import patch, MagicMock, PropertyMock

from hpipe.core.hutils import system
from hpipe.assets import reviewable, projectFile, asset
from hpipe.core import constants


# ---------------------------------------------------------------------------
# Helpers — build lightweight mocks without touching disk or DB
# ---------------------------------------------------------------------------

def _make_mock_directory(path: str, exists: bool = True, children: list = None):
    """Create a mock system.Directory that doesn't touch the filesystem."""
    d = MagicMock()
    d.directory_path = path
    d.system_path.return_value = path
    d.exists.return_value = exists
    d.get_children_directories.return_value = children or []
    d.get_basename.return_value = os.path.basename(path)
    return d


def _make_mock_filepath(path: str, exists: bool = True):
    """Create a mock system.Filepath."""
    f = MagicMock(spec=system.Filepath)
    f.filepath_path = path
    f.system_path.return_value = path
    f.exists.return_value = exists
    f.get_extension.return_value = path.rsplit('.', 1)[-1] if '.' in path else ''
    f.get_filename.return_value = os.path.basename(path).rsplit('.', 1)[0]
    f.get_parent_directory.return_value = _make_mock_directory(os.path.dirname(path))
    f.basename = os.path.basename(path)
    return f


def _make_mock_shot(shot_name: str = "SH010",
                    project_name: str = "test_project",
                    comps_exist: bool = True,
                    plates_exist: bool = True,
                    renders_exist: bool = True,
                    workarea_exist: bool = True,
                    ref_exist: bool = True,
                    nuke_files: list = None,
                    houdini_files: list = None):
    """
    Build a mock Shot object with controllable directory existence.
    """
    from hpipe.core import shot as shot_module

    base = f"Y:/projects/2023/{project_name}/shots"
    shot_path = f"{base}/{shot_name}"

    mock_shot = MagicMock(spec=shot_module.Shot)
    mock_shot.name = shot_name
    mock_shot.base_path = base

    # get_shot_path returns a plain string
    mock_shot.get_shot_path.return_value = shot_path

    # --- Comp ---
    comp_dir = _make_mock_directory(
        f"{shot_path}/{constants.OUTPUT_FOLDER}/{constants.COMP_FOLDER}",
        exists=comps_exist,
        children=[
            _make_mock_directory(f"{shot_path}/output/comp/comp_v001"),
            _make_mock_directory(f"{shot_path}/output/comp/comp_v002"),
        ] if comps_exist else [],
    )
    mock_shot.get_comps_path.return_value = comp_dir

    # get_comps uses reviewable.reviewables_from_directory internally.
    # We'll let the real function be tested via reviewables_from_directory tests.
    # Here we simulate what the real shot.get_comps() would return.
    if comps_exist:
        mock_shot.get_comps.return_value = [
            _make_sequence_reviewable("comp_v001", f"{shot_path}/output/comp/comp_v001"),
            _make_sequence_reviewable("comp_v002", f"{shot_path}/output/comp/comp_v002"),
        ]
    else:
        mock_shot.get_comps.side_effect = FileNotFoundError(
            f"[Errno 2] No such file or directory: '{comp_dir.directory_path}'"
        )

    # --- Plate ---
    plate_dir = _make_mock_directory(
        f"{shot_path}/{constants.PLATE_FOLDER}",
        exists=plates_exist,
        children=[
            _make_mock_directory(f"{shot_path}/plate/plate_v001"),
        ] if plates_exist else [],
    )
    mock_shot.get_plate_path.return_value = plate_dir

    if plates_exist:
        mock_shot.get_plates.return_value = [
            _make_sequence_reviewable("plate_v001", f"{shot_path}/plate/plate_v001"),
        ]
    else:
        mock_shot.get_plates.side_effect = FileNotFoundError(
            f"[Errno 2] No such file or directory: '{plate_dir.directory_path}'"
        )

    # --- Render ---
    render_dir = _make_mock_directory(
        f"{shot_path}/{constants.OUTPUT_FOLDER}/{constants.RENDER_FOLDER}",
        exists=renders_exist,
        children=[
            _make_mock_directory(f"{shot_path}/output/render/beauty"),
            _make_mock_directory(f"{shot_path}/output/render/deep"),
        ] if renders_exist else [],
    )
    mock_shot.get_render_path.return_value = render_dir

    # --- Workarea ---
    workarea_dir = _make_mock_directory(
        f"{shot_path}/{constants.OUTPUT_FOLDER}/{constants.WORKAREA_FOLDER}",
        exists=workarea_exist,
        children=[
            _make_mock_directory(f"{shot_path}/output/_workarea/wip_v001"),
        ] if workarea_exist else [],
    )
    mock_shot.get_workarea_path.return_value = workarea_dir

    # --- Nuke path / Houdini path (for project files) ---
    mock_shot.get_nuke_path.return_value = _make_mock_directory(
        f"{shot_path}/{constants.WORKING_FOLDER}/{constants.NUKE_FOLDER}"
    )
    mock_shot.get_houdini_path.return_value = _make_mock_directory(
        f"{shot_path}/{constants.WORKING_FOLDER}/{constants.HOUDINI_FOLDER}"
    )

    # get_project_files
    pf_list = []
    for nk in (nuke_files or []):
        pf = MagicMock(spec=projectFile.NukeProjectFile)
        pf.filepath = _make_mock_filepath(nk)
        pf.asset_name = os.path.basename(nk).rsplit('.', 1)[0]
        pf.asset_type = asset.AssetType.PROJECT_FILE
        pf.to_dict.return_value = {"asset_name": pf.asset_name, "filepath": nk}
        pf_list.append(pf)
    for hip in (houdini_files or []):
        pf = MagicMock(spec=projectFile.HoudiniProjectFile)
        pf.filepath = _make_mock_filepath(hip)
        pf.asset_name = os.path.basename(hip).rsplit('.', 1)[0]
        pf.asset_type = asset.AssetType.PROJECT_FILE
        pf.to_dict.return_value = {"asset_name": pf.asset_name, "filepath": hip}
        pf_list.append(pf)
    mock_shot.get_project_files.return_value = pf_list

    return mock_shot


def _make_sequence_reviewable(name: str, path: str):
    """Create a mock SequenceReviewable."""
    r = MagicMock(spec=reviewable.SequenceReviewable)
    r.asset_name = name
    r.reviewable_directory = _make_mock_directory(path)
    r.get_thumbnail_image.return_value = None
    return r


# ═══════════════════════════════════════════════════════════════════════════
# 1. TESTS FOR reviewable.reviewables_from_directory
#    This is the core factory — if it fails, no type works.
# ═══════════════════════════════════════════════════════════════════════════

class TestReviewablesFromDirectory:
    """Tests for reviewable.reviewables_from_directory()."""

    def test_returns_one_reviewable_per_subdirectory(self):
        """Each child directory should become one SequenceReviewable."""
        parent = _make_mock_directory("Y:/projects/2023/test/shots/SH010/output/comp",
                                      children=[
                                          _make_mock_directory("Y:/proj/comp/comp_v001"),
                                          _make_mock_directory("Y:/proj/comp/comp_v002"),
                                          _make_mock_directory("Y:/proj/comp/comp_v003"),
                                      ])
        with patch.object(system.Directory, 'get_children_directories',
                          return_value=parent.get_children_directories()):
            result = reviewable.reviewables_from_directory(parent)

        assert len(result) == 3, f"Expected 3 reviewables, got {len(result)}"
        for r in result:
            assert isinstance(r, reviewable.SequenceReviewable)

    def test_empty_directory_returns_empty_list(self):
        """A directory with no subdirectories should return []."""
        parent = _make_mock_directory("Y:/proj/render", children=[])
        with patch.object(system.Directory, 'get_children_directories', return_value=[]):
            result = reviewable.reviewables_from_directory(parent)
        assert result == []

    def test_nonexistent_directory_raises(self):
        """
        BUG DIAGNOSTIC: If the directory doesn't exist, get_children_directories
        calls os.listdir which raises FileNotFoundError. This is why Plates /
        Renders / etc. silently fail — the exception is caught and swallowed by
        get_reviewables().
        """
        bad_dir = system.Directory.__new__(system.Directory)
        bad_dir.directory_path = "Y:/does/not/exist"
        bad_dir.force_raw_path = True

        with pytest.raises(FileNotFoundError):
            # os.listdir inside get_children_directories will raise
            bad_dir.get_children_directories()


# ═══════════════════════════════════════════════════════════════════════════
# 2. TESTS FOR shot path construction
#    Verify each shot method builds the expected filesystem path.
# ═══════════════════════════════════════════════════════════════════════════

class TestShotPathConstruction:
    """
    Verify that Shot's path methods produce the correct directory objects.
    These paths are what get_reviewables ultimately tries to list.
    """

    @pytest.fixture
    def mock_project(self):
        from hpipe.core import project as project_module
        p = MagicMock(spec=project_module.Project)
        p.name = "myshow"
        p.get_project_path.return_value = "Y:/projects/2023/myshow"
        return p

    @pytest.fixture
    def real_shot(self, mock_project):
        """
        Build a real Shot object with a mocked project so we can test the
        actual path-construction logic.
        """
        from hpipe.core import shot as shot_module
        s = shot_module.Shot.__new__(shot_module.Shot)
        s.name = "SH010"
        s.project = mock_project
        s.frame_start = 1000
        s.frame_end = 1100
        s.tags = []
        s.user_data = {}
        s.base_path = f"{mock_project.get_project_path()}/{constants.SHOT_FOLDER}/"
        return s

    def test_comp_path(self, real_shot):
        comp_dir = real_shot.get_comps_path()
        expected = "output/comp"
        assert expected in comp_dir.directory_path, \
            f"Comp path should contain '{expected}', got: {comp_dir.directory_path}"

    def test_plate_path(self, real_shot):
        plate_dir = real_shot.get_plate_path()
        assert "plate" in plate_dir.directory_path, \
            f"Plate path should contain 'plate', got: {plate_dir.directory_path}"

    def test_render_path(self, real_shot):
        render_dir = real_shot.get_render_path()
        expected = "output/render"
        assert expected in render_dir.directory_path, \
            f"Render path should contain '{expected}', got: {render_dir.directory_path}"

    def test_workarea_path(self, real_shot):
        wa_dir = real_shot.get_workarea_path()
        expected = "output/_workarea"
        assert expected in wa_dir.directory_path, \
            f"Workarea path should contain '{expected}', got: {wa_dir.directory_path}"

    def test_nuke_path(self, real_shot):
        nuke_dir = real_shot.get_nuke_path()
        expected = "working_files/nuke"
        assert expected in nuke_dir.directory_path, \
            f"Nuke path should contain '{expected}', got: {nuke_dir.directory_path}"

    def test_houdini_path(self, real_shot):
        hou_dir = real_shot.get_houdini_path()
        expected = "working_files/houdini"
        assert expected in hou_dir.directory_path, \
            f"Houdini path should contain '{expected}', got: {hou_dir.directory_path}"

    def test_all_paths_share_common_base(self, real_shot):
        """Every output path should start with the same shot base."""
        paths = [
            real_shot.get_comps_path().directory_path,
            real_shot.get_plate_path().directory_path,
            real_shot.get_render_path().directory_path,
            real_shot.get_workarea_path().directory_path,
        ]
        for p in paths:
            assert real_shot.name in p, \
                f"Path '{p}' does not contain shot name '{real_shot.name}'"


# ═══════════════════════════════════════════════════════════════════════════
# 3. TESTS FOR get_reviewables — the main dispatcher
#    These expose exactly why non-Comp types return nothing.
# ═══════════════════════════════════════════════════════════════════════════

class TestGetReviewables:
    """
    Tests for output_utils.get_reviewables().

    We patch reviewable.reviewables_from_directory so we don't hit disk,
    and instead verify that get_reviewables correctly dispatches to the
    right shot methods and returns the results.
    """

    def _import_get_reviewables(self):
        """Import lazily to avoid module-level PySide6 / DB side effects."""
        from hpipe.apps.pipeDisplay import output_utils
        return output_utils.get_reviewables

    # -- Comp (the one that works) --

    def test_comp_returns_reviewables(self):
        get_reviewables = self._import_get_reviewables()
        shot = _make_mock_shot(comps_exist=True)
        result = get_reviewables([shot], "Comp", "")
        assert result is not None
        assert len(result) == 2, f"Expected 2 comps, got {len(result)}"
        shot.get_comps.assert_called_once()

    # -- Plate --

    def test_plate_returns_reviewables_when_dir_exists(self):
        get_reviewables = self._import_get_reviewables()
        shot = _make_mock_shot(plates_exist=True)
        result = get_reviewables([shot], "Plate", "")
        assert result is not None
        assert len(result) == 1, f"Expected 1 plate, got {len(result)}"
        shot.get_plates.assert_called_once()

    def test_plate_silent_failure_when_dir_missing(self):
        """
        BUG: When the plate directory doesn't exist on disk,
        shot.get_plates() → reviewables_from_directory() → os.listdir()
        raises FileNotFoundError.  get_reviewables catches it silently,
        returning an empty list instead of reporting the error.
        """
        get_reviewables = self._import_get_reviewables()
        shot = _make_mock_shot(plates_exist=False)
        result = get_reviewables([shot], "Plate", "")
        # The exception is caught — we get an empty list, NOT None
        assert result is not None
        assert len(result) == 0, \
            "Plate returned results despite the directory not existing — " \
            "check whether the exception is properly handled"

    # -- Renders --

    def test_renders_calls_reviewables_from_directory(self):
        """
        BUG DIAGNOSTIC: Renders uses render_dir.exists() before calling
        reviewables_from_directory.  If exists() returns True, the factory
        should be called.
        """
        get_reviewables = self._import_get_reviewables()
        shot = _make_mock_shot(renders_exist=True)

        with patch("hpipe.apps.pipeDisplay.output_utils.reviewable.reviewables_from_directory") as mock_factory:
            mock_factory.return_value = [
                _make_sequence_reviewable("beauty", "Y:/proj/render/beauty"),
            ]
            result = get_reviewables([shot], "Renders", "")

        assert result is not None
        assert len(result) == 1, f"Expected 1 render, got {len(result)}"
        mock_factory.assert_called_once()

    def test_renders_skipped_when_dir_missing(self):
        """When render dir doesn't exist, should return empty — not crash."""
        get_reviewables = self._import_get_reviewables()
        shot = _make_mock_shot(renders_exist=False)

        with patch("hpipe.apps.pipeDisplay.output_utils.reviewable.reviewables_from_directory") as mock_factory:
            result = get_reviewables([shot], "Renders", "")

        assert result is not None
        assert len(result) == 0
        mock_factory.assert_not_called()

    # -- Workarea --

    def test_workarea_returns_reviewables(self):
        get_reviewables = self._import_get_reviewables()
        shot = _make_mock_shot(workarea_exist=True)

        with patch("hpipe.apps.pipeDisplay.output_utils.reviewable.reviewables_from_directory") as mock_factory:
            mock_factory.return_value = [
                _make_sequence_reviewable("wip_v001", "Y:/proj/workarea/wip_v001"),
            ]
            result = get_reviewables([shot], "Workarea", "")

        assert len(result) == 1
        mock_factory.assert_called_once()

    def test_workarea_skipped_when_missing(self):
        get_reviewables = self._import_get_reviewables()
        shot = _make_mock_shot(workarea_exist=False)

        with patch("hpipe.apps.pipeDisplay.output_utils.reviewable.reviewables_from_directory") as mock_factory:
            result = get_reviewables([shot], "Workarea", "")

        assert len(result) == 0
        mock_factory.assert_not_called()

    # -- Ref --

    def test_ref_constructs_correct_path(self):
        """
        BUG DIAGNOSTIC: Ref builds system.Directory(f'{shot_path}/ref').
        If shot_path has a trailing slash this could produce a double slash,
        or the Directory constructor could fail if the path doesn't exist.
        """
        get_reviewables = self._import_get_reviewables()
        shot = _make_mock_shot(ref_exist=True)

        with patch("hpipe.apps.pipeDisplay.output_utils.system.Directory") as MockDir, \
             patch("hpipe.apps.pipeDisplay.output_utils.reviewable.reviewables_from_directory") as mock_factory:
            mock_dir_instance = MagicMock()
            mock_dir_instance.directory_path = "Y:/proj/SH010/ref"
            mock_dir_instance.exists.return_value = True
            MockDir.return_value = mock_dir_instance
            mock_factory.return_value = [_make_sequence_reviewable("ref_plate", "Y:/proj/ref/ref_plate")]

            result = get_reviewables([shot], "Ref", "")

        # Verify the Directory was constructed with the shot path + /ref
        call_args = MockDir.call_args[0][0]
        assert "ref" in call_args, f"Ref path should contain 'ref', got: {call_args}"
        assert len(result) == 1

    def test_ref_directory_constructor_may_fail(self):
        """
        BUG: system.Directory() constructor calls system_path() which calls
        Filepath().get_path_system() — this raises ValueError if the path
        doesn't match any known system root (Y:, /mnt/share, etc.).
        If the shot_path is somehow malformed, Ref will silently fail.
        """
        get_reviewables = self._import_get_reviewables()
        shot = _make_mock_shot()
        # Make get_shot_path return something weird
        shot.get_shot_path.return_value = "/invalid/root/SH010"

        with patch("hpipe.apps.pipeDisplay.output_utils.system.Directory") as MockDir:
            MockDir.side_effect = ValueError("Filepath does not contain a valid system root.")
            result = get_reviewables([shot], "Ref", "")

        # The ValueError is caught by the try/except — silent failure
        assert len(result) == 0

    # -- Project Files --

    def test_project_files_wraps_in_adapter(self):
        get_reviewables = self._import_get_reviewables()
        shot = _make_mock_shot(
            nuke_files=["Y:/proj/nuke/SH010-comp-main-A01.nk"],
            houdini_files=["Y:/proj/houdini/SH010-fx-sim-A01.hipnc"],
        )

        with patch("hpipe.apps.pipeDisplay.output_utils.reviewable.ProjectFileReviewable") as MockPFR:
            MockPFR.side_effect = lambda pf: _make_sequence_reviewable(pf.asset_name, "dummy")
            result = get_reviewables([shot], "Project Files", "")

        assert len(result) == 2, f"Expected 2 project files, got {len(result)}"
        assert MockPFR.call_count == 2

    def test_project_files_empty_when_no_files(self):
        get_reviewables = self._import_get_reviewables()
        shot = _make_mock_shot(nuke_files=[], houdini_files=[])
        result = get_reviewables([shot], "Project Files", "")
        assert len(result) == 0

    # -- None / empty inputs --

    def test_none_shot_list_returns_none(self):
        get_reviewables = self._import_get_reviewables()
        result = get_reviewables(None, "Comp", "")
        assert result is None

    def test_empty_shot_list_returns_none(self):
        """Empty list is falsy — get_reviewables returns None."""
        get_reviewables = self._import_get_reviewables()
        result = get_reviewables([], "Comp", "")
        assert result is None

    def test_unknown_type_returns_empty(self):
        get_reviewables = self._import_get_reviewables()
        shot = _make_mock_shot()
        result = get_reviewables([shot], "NonexistentType", "")
        assert result is not None
        assert len(result) == 0

    # -- Filter --

    def test_filter_narrows_results(self):
        get_reviewables = self._import_get_reviewables()
        shot = _make_mock_shot(comps_exist=True)
        # Default mock returns comp_v001 and comp_v002
        result = get_reviewables([shot], "Comp", "v001")
        assert len(result) == 1
        assert "v001" in result[0].asset_name

    def test_filter_case_insensitive(self):
        get_reviewables = self._import_get_reviewables()
        shot = _make_mock_shot(comps_exist=True)
        result = get_reviewables([shot], "Comp", "V001")
        assert len(result) == 1

    # -- Multiple shots --

    def test_multiple_shots_accumulate(self):
        get_reviewables = self._import_get_reviewables()
        shot_a = _make_mock_shot("SH010", comps_exist=True)
        shot_b = _make_mock_shot("SH020", comps_exist=True)
        result = get_reviewables([shot_a, shot_b], "Comp", "")
        assert len(result) == 4, f"Expected 4 comps (2 per shot), got {len(result)}"

    def test_one_bad_shot_doesnt_block_others(self):
        """
        BUG DIAGNOSTIC: If one shot throws (e.g. missing directory),
        the other shots should still contribute their reviewables.
        """
        get_reviewables = self._import_get_reviewables()
        good_shot = _make_mock_shot("SH010", comps_exist=True)
        bad_shot = _make_mock_shot("SH020", comps_exist=False)  # will raise
        result = get_reviewables([good_shot, bad_shot], "Comp", "")
        # good_shot returns 2, bad_shot throws (caught) → total should be 2
        assert len(result) == 2, \
            f"Expected 2 comps from the good shot, got {len(result)}"


# ═══════════════════════════════════════════════════════════════════════════
# 4. TESTS FOR ProjectFileReviewable adapter
# ═══════════════════════════════════════════════════════════════════════════

class TestProjectFileReviewable:

    def _make_nuke_file(self, path="Y:/proj/nuke/SH010-comp-A01.nk"):
        pf = MagicMock(spec=projectFile.NukeProjectFile)
        pf.filepath = _make_mock_filepath(path)
        pf.asset_name = "SH010-comp-A01"
        pf.asset_type = asset.AssetType.PROJECT_FILE
        pf.to_dict.return_value = {"asset_name": pf.asset_name, "filepath": path}
        return pf

    def test_wraps_project_file(self):
        pf = self._make_nuke_file()
        r = reviewable.ProjectFileReviewable(pf)
        assert r.asset_name == "SH010-comp-A01"
        assert r.asset_type == asset.AssetType.PROJECT_FILE

    def test_thumbnail_always_none(self):
        """Project files have no image — thumbnail should be None (fallback icon)."""
        pf = self._make_nuke_file()
        r = reviewable.ProjectFileReviewable(pf)
        assert r.get_thumbnail_image() is None

    def test_generate_thumbnail_returns_none(self):
        pf = self._make_nuke_file()
        r = reviewable.ProjectFileReviewable(pf)
        assert r.generate_thumbnail(_make_mock_filepath("dummy.jpg")) is None

    def test_get_filepath_delegates(self):
        pf = self._make_nuke_file()
        r = reviewable.ProjectFileReviewable(pf)
        assert r.get_filepath() == pf.filepath

    def test_rejects_non_project_file(self):
        """Should raise TypeError if passed something that isn't a GenericProjectFile."""
        not_a_pf = MagicMock()
        not_a_pf.__class__ = str  # definitely not GenericProjectFile
        with pytest.raises(TypeError):
            reviewable.ProjectFileReviewable(not_a_pf)

    def test_uses_filename_when_asset_name_empty(self):
        pf = self._make_nuke_file()
        pf.asset_name = ""
        r = reviewable.ProjectFileReviewable(pf)
        # Should fall back to filepath.get_filename()
        assert r.asset_name != "", "Should have fallen back to filename"


# ═══════════════════════════════════════════════════════════════════════════
# 5. TESTS FOR Directory.exists() — the guard that Renders/Workarea use
# ═══════════════════════════════════════════════════════════════════════════

class TestDirectoryExists:
    """
    Verify that Directory.exists() actually works, since Renders, Workarea,
    and Ref all depend on it to decide whether to scan.
    """

    def test_exists_returns_false_for_missing_dir(self):
        with patch("os.path.exists", return_value=False):
            d = system.Directory.__new__(system.Directory)
            d.directory_path = "Y:/nonexistent/path"
            assert d.exists() is False

    def test_exists_returns_true_for_real_dir(self):
        with patch("os.path.exists", return_value=True):
            d = system.Directory.__new__(system.Directory)
            d.directory_path = "Y:/real/path"
            assert d.exists() is True


# ═══════════════════════════════════════════════════════════════════════════
# 6. DIAGNOSTIC TESTS — explain the root cause
# ═══════════════════════════════════════════════════════════════════════════

class TestDiagnosticRootCause:
    """
    These tests document the specific bugs that cause non-Comp types to fail.
    """

    def test_get_comps_has_no_exists_guard(self):
        """
        shot.get_comps() calls reviewables_from_directory() with NO exists()
        check.  If the comp dir is missing, it raises FileNotFoundError.

        This means comps only work because the directories actually exist on
        disk. Every other type that ALSO lacks a guard will fail the same way.
        """
        from hpipe.core import shot as shot_module
        mock_project = MagicMock()
        mock_project.get_project_path.return_value = "Y:/projects/2023/test"
        s = shot_module.Shot.__new__(shot_module.Shot)
        s.name = "SH010"
        s.project = mock_project
        s.base_path = "Y:/projects/2023/test/shots/"

        # Patch os.listdir to simulate missing directory
        with patch("os.listdir", side_effect=FileNotFoundError("No such dir")):
            with pytest.raises(FileNotFoundError):
                s.get_comps()

    def test_get_plates_has_no_exists_guard(self):
        """
        Same as comps — get_plates() has no exists() guard.
        If the plate dir is missing, FileNotFoundError propagates up.
        """
        from hpipe.core import shot as shot_module
        mock_project = MagicMock()
        mock_project.get_project_path.return_value = "Y:/projects/2023/test"
        s = shot_module.Shot.__new__(shot_module.Shot)
        s.name = "SH010"
        s.project = mock_project
        s.base_path = "Y:/projects/2023/test/shots/"

        with patch("os.listdir", side_effect=FileNotFoundError("No such dir")):
            with pytest.raises(FileNotFoundError):
                s.get_plates()

    def test_silent_exception_swallowing_in_get_reviewables(self):
        """
        CORE BUG: get_reviewables wraps each shot in try/except Exception,
        which catches FileNotFoundError, ValueError, etc.  This means:

        1. If plate/render/workarea directories don't exist, the error is
           silently swallowed and the user sees 0 results with no warning.
        2. If system.Directory() raises ValueError (bad path root), same thing.
        3. Only Comp works because those directories happen to exist on disk.

        The fix should either:
        (a) Add exists() guards in shot.get_comps() / get_plates() so they
            return [] instead of raising, OR
        (b) Log the exceptions at WARNING level so they're visible.
        """
        get_reviewables = self._import_get_reviewables()
        shot = MagicMock()
        shot.get_plates.side_effect = FileNotFoundError("plate dir missing")

        # This should NOT crash — the exception is caught
        result = get_reviewables([shot], "Plate", "")
        assert result is not None
        assert len(result) == 0
        # But the user sees nothing — no error, no plates. Silent failure.

    def _import_get_reviewables(self):
        from hpipe.apps.pipeDisplay import output_utils
        return output_utils.get_reviewables

    def test_renders_exists_guard_works_correctly(self):
        """
        Renders DOES have an exists() guard — but only in get_reviewables,
        not in shot.get_render_path(). The guard prevents the crash but
        returns empty when the directory is missing. This is correct behavior
        but the user gets no feedback about WHY renders are empty.
        """
        get_reviewables = self._import_get_reviewables()
        shot = _make_mock_shot(renders_exist=False)
        result = get_reviewables([shot], "Renders", "")
        assert len(result) == 0
        # No crash, but also no indication that the render dir doesn't exist.
