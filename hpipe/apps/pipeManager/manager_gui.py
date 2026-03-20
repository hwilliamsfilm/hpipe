"""
Pipe Manager GUI for managing projects, shots, and assets.
"""

import sys
if sys.version_info <= (3, 8):
    from PySide2 import QtWidgets, QtCore, QtGui
    from typing_extensions import TypedDict, Literal, overload
else:
    from PySide6 import QtWidgets, QtCore, QtGui

import hpipe.core.project
from hpipe.core import data_manager, project, shot
from hpipe.apps.pipeManager import pipe_widgets
from hpipe.apps.pipeManager import manager_utils
from hpipe.apps import style
from hpipe.core.hutils import logger
from typing import *

log = logger.setup_logger()
log.debug("manager_gui.py loaded")


class ProjectDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create Project")
        self.setStyleSheet(style.WINDOW_STYLE)
        self.setMinimumWidth(400)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        layout.addWidget(QtWidgets.QLabel("<b>New Project</b>"))
        layout.addWidget(_hline())

        form = QtWidgets.QFormLayout()
        form.setLabelAlignment(QtCore.Qt.AlignRight)  # type: ignore
        form.setSpacing(8)
        self._name_input = QtWidgets.QLineEdit()
        self._name_input.setPlaceholderText("my_project")
        self._desc_input = QtWidgets.QLineEdit()
        self._desc_input.setPlaceholderText("Brief description")
        form.addRow("Project Name:", self._name_input)
        form.addRow("Description:", self._desc_input)
        layout.addLayout(form)

        layout.addWidget(_hline())
        btn_row = QtWidgets.QHBoxLayout()
        btn_row.addStretch()
        cancel_btn = QtWidgets.QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        self._create_btn = QtWidgets.QPushButton("Create")
        self._create_btn.setStyleSheet(style.ACCENT_BUTTON_STYLE)
        self._create_btn.setDefault(True)
        self._create_btn.clicked.connect(self._validate_and_accept)
        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(self._create_btn)
        layout.addLayout(btn_row)

    def _validate_and_accept(self):
        if not self._name_input.text().strip():
            QtWidgets.QMessageBox.warning(self, "Validation", "Project name cannot be empty.")
            return
        self.accept()

    def get_answers(self) -> dict:
        return {
            "Project Name": self._name_input.text().strip(),
            "Project Description": self._desc_input.text().strip(),
        }


class ShotDialog(QtWidgets.QDialog):
    def __init__(self, parent=None, project_for_shot=None):
        super().__init__(parent)
        project_name = project_for_shot.name if project_for_shot else "Unknown"
        self.setWindowTitle(f"Create Shot in {project_name}")
        self.setStyleSheet(style.WINDOW_STYLE)
        self.setMinimumWidth(360)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        layout.addWidget(QtWidgets.QLabel(f"<b>New Shot — {project_name}</b>"))
        layout.addWidget(_hline())

        form = QtWidgets.QFormLayout()
        form.setLabelAlignment(QtCore.Qt.AlignRight)  # type: ignore
        form.setSpacing(8)
        self._name_input = QtWidgets.QLineEdit()
        self._name_input.setPlaceholderText("sh010")
        self._start_input = QtWidgets.QLineEdit("1001")
        self._end_input = QtWidgets.QLineEdit("1100")
        form.addRow("Shot Name:", self._name_input)
        form.addRow("Start Frame:", self._start_input)
        form.addRow("End Frame:", self._end_input)
        layout.addLayout(form)

        layout.addWidget(_hline())
        btn_row = QtWidgets.QHBoxLayout()
        btn_row.addStretch()
        cancel_btn = QtWidgets.QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        create_btn = QtWidgets.QPushButton("Create")
        create_btn.setStyleSheet(style.ACCENT_BUTTON_STYLE)
        create_btn.setDefault(True)
        create_btn.clicked.connect(self._validate_and_accept)
        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(create_btn)
        layout.addLayout(btn_row)

    def _validate_and_accept(self):
        if not self._name_input.text().strip():
            QtWidgets.QMessageBox.warning(self, "Validation", "Shot name cannot be empty.")
            return
        for label, widget in [("Start Frame", self._start_input), ("End Frame", self._end_input)]:
            try:
                int(widget.text())
            except ValueError:
                QtWidgets.QMessageBox.warning(self, "Validation", f"{label} must be an integer.")
                return
        self.accept()

    def get_answers(self) -> dict:
        return {
            "Shot Name": self._name_input.text().strip(),
            "Start Frame": self._start_input.text().strip(),
            "End Frame": self._end_input.text().strip(),
        }


def _hline() -> QtWidgets.QFrame:
    line = QtWidgets.QFrame()
    line.setFrameShape(QtWidgets.QFrame.HLine)
    line.setFrameShadow(QtWidgets.QFrame.Sunken)
    return line


class ProjectOverview(QtWidgets.QWidget):
    """
    Project Overview Panel — view and manage all projects and shots.
    """
    def __init__(self,
                 parent=None,
                 font_scale: float = 1.0,
                 file_dropper: bool = True,
                 sidebar: bool = True,
                 commit_selection: bool = False):

        super(ProjectOverview, self).__init__(parent)

        self.setStyleSheet(style.WINDOW_STYLE)
        self.setWindowTitle("Project Manager")
        self.resize(int(1920 / 1.5), int(1080 / 1.5))

        # ── Fonts & colours ────────────────────────────────────────────────
        self.tree_color = style.TREE_SECONDARY
        self.shot_color = style.SHOT_COLOR
        self.project_color = style.PROJECT_COLOR
        self.date_color = style.DATE_COLOR
        self.primary_tree = style.TREE_PRIMARY
        self.secondary_tree = style.TREE_SECONDARY

        # ── Header ─────────────────────────────────────────────────────────
        title_layout = QtWidgets.QHBoxLayout()
        icon_label = QtWidgets.QLabel()
        icon_label.setFixedSize(36, 36)
        icon_pix = QtGui.QPixmap(style.icon_path("germ.png"))
        icon_label.setPixmap(icon_pix.scaled(36, 36, QtCore.Qt.KeepAspectRatio,  # type: ignore
                                             QtCore.Qt.SmoothTransformation))  # type: ignore
        title_label = QtWidgets.QLabel("Project Manager")
        title_label.setFont(style.title_font(font_scale))
        title_layout.addWidget(icon_label)
        title_layout.addWidget(title_label)
        title_layout.addStretch()

        subtitle = QtWidgets.QLabel("'Chaos is just order waiting to be discovered.'")
        subtitle.setFont(style.subtitle_font(font_scale))
        subtitle.setStyleSheet(f"color: {style.TEXT_SECONDARY};")

        self.setWindowIcon(QtGui.QIcon(style.icon_path("germ.png")))

        # ── Sort bar ───────────────────────────────────────────────────────
        sort_layout = QtWidgets.QHBoxLayout()
        sort_layout.setAlignment(QtCore.Qt.AlignRight)  # type: ignore
        sort_label = QtWidgets.QLabel("Sort By:")
        sort_label.setFont(style.small_font(font_scale))
        self.sort_by_dropdown = QtWidgets.QComboBox()
        self.sort_by_dropdown.addItems(manager_utils.Constants().SORTING_TYPES)
        self.sort_by_dropdown.setFont(style.small_font(font_scale))
        self.sort_by_dropdown.setFixedWidth(200)

        self.refresh_button = QtWidgets.QPushButton()
        refresh_pix = QtGui.QPixmap(style.icon_path("cupcake.png"))
        self.refresh_button.setIcon(QtGui.QIcon(refresh_pix))
        self.refresh_button.setIconSize(QtCore.QSize(20, 20))
        self.refresh_button.setFixedSize(32, 32)
        self.refresh_button.setFlat(True)
        self.refresh_button.setToolTip("Refresh")
        self.refresh_button.setCursor(QtCore.Qt.PointingHandCursor)  # type: ignore

        sort_layout.addWidget(sort_label)
        sort_layout.addWidget(self.sort_by_dropdown)
        sort_layout.addWidget(self.refresh_button)

        # ── Tree ───────────────────────────────────────────────────────────
        self.tree = QtWidgets.QTreeWidget()
        self.tree.setColumnCount(4)
        self.tree.setHeaderHidden(True)
        self.tree.setFont(style.tree_font(font_scale))
        self.tree.header().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)  # type: ignore
        self.tree.header().setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)  # type: ignore
        self.tree.header().setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeToContents)  # type: ignore
        self.tree.setAlternatingRowColors(True)
        self.tree.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)  # type: ignore
        self.tree.setUniformRowHeights(True)
        self.tree.setItemDelegate(pipe_widgets.EditableDelegate())

        tree_container = QtWidgets.QVBoxLayout()
        tree_container.addLayout(sort_layout)
        tree_container.addWidget(self.tree)

        tree_body = QtWidgets.QHBoxLayout()
        tree_body.addLayout(tree_container)

        # ── Sidebar buttons ────────────────────────────────────────────────
        self.button_layout = QtWidgets.QVBoxLayout()
        self.button_layout.setSpacing(6)
        self.button_layout.setAlignment(QtCore.Qt.AlignTop)  # type: ignore

        def _make_btn(label: str, danger: bool = False) -> QtWidgets.QPushButton:
            btn = QtWidgets.QPushButton(label)
            btn.setFixedHeight(36)
            btn.setMinimumWidth(160)
            btn.setFont(style.button_font(font_scale))
            if danger:
                btn.setStyleSheet(style.DANGER_BUTTON_STYLE)
            return btn

        sep_projects = QtWidgets.QLabel("PROJECTS")
        sep_projects.setStyleSheet(style.SIDEBAR_LABEL_STYLE)
        self.button_layout.addWidget(sep_projects)
        self.add_project_button = _make_btn("Add Project")
        self.remove_project_button = _make_btn("Remove Project", danger=True)
        self.button_layout.addWidget(self.add_project_button)
        self.button_layout.addWidget(self.remove_project_button)

        self.button_layout.addSpacing(8)
        sep_shots = QtWidgets.QLabel("SHOTS")
        sep_shots.setStyleSheet(style.SIDEBAR_LABEL_STYLE)
        self.button_layout.addWidget(sep_shots)
        self.add_shot_button = _make_btn("Add Shot")
        self.remove_shot_button = _make_btn("Remove Shot", danger=True)
        self.add_shot_tags_button = _make_btn("Add Shot Tags")
        self.remove_shot_tags_button = _make_btn("Remove Shot Tags", danger=True)
        self.button_layout.addWidget(self.add_shot_button)
        self.button_layout.addWidget(self.remove_shot_button)
        self.button_layout.addWidget(self.add_shot_tags_button)
        self.button_layout.addWidget(self.remove_shot_tags_button)

        self.button_layout.addSpacing(8)
        self.save_button = _make_btn("Save")
        self.save_button.setStyleSheet(style.ACCENT_BUTTON_STYLE)
        self.button_layout.addWidget(self.save_button)

        if sidebar:
            tree_body.addLayout(self.button_layout)

        # ── Drag & Drop ────────────────────────────────────────────────────
        self.drag_drop_button = QtWidgets.QPushButton("Drag and drop files here to ingest")
        self.drag_drop_button.setStyleSheet(style.DRAG_DROP_STYLE)
        self.drag_drop_button.setFixedHeight(80)
        self.drag_drop_button.setFont(style.small_font(font_scale))
        self.drag_drop_button.setAcceptDrops(True)
        self.drag_drop_button.dragEnterEvent = self.dragEnterEvent  # type: ignore
        self.drag_drop_button.dropEvent = self.dropEvent  # type: ignore

        self.drag_drop_combo = QtWidgets.QComboBox()
        self.drag_drop_combo.addItems(manager_utils.Constants().INGEST_LOCATIONS)
        self.drag_drop_combo.setFixedHeight(32)
        self.drag_drop_combo.setFixedWidth(180)
        self.drag_drop_combo.setFont(style.small_font(font_scale))

        self.loading_bar = QtWidgets.QProgressBar()
        self.loading_bar.setFixedHeight(6)
        self.loading_bar.setFixedWidth(180)
        self.loading_bar.setTextVisible(False)
        self.loading_bar.setValue(0)

        dd_side = QtWidgets.QVBoxLayout()
        dd_side.addWidget(self.drag_drop_combo)
        dd_side.addWidget(self.loading_bar)
        dd_side.setAlignment(QtCore.Qt.AlignVCenter)  # type: ignore

        dd_row = QtWidgets.QHBoxLayout()
        dd_row.addWidget(self.drag_drop_button, stretch=1)
        dd_row.addLayout(dd_side)

        # ── Status bar ─────────────────────────────────────────────────────
        self.status_label = QtWidgets.QLabel()
        self.status_label.setFont(style.small_font(font_scale))
        self.status_label.setStyleSheet(f"color: {style.TEXT_SECONDARY};")
        self.status_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)  # type: ignore

        # ── Commit selection ───────────────────────────────────────────────
        self.commit_selection_button = QtWidgets.QPushButton("Select Shot")
        self.commit_selection_button.setFixedHeight(36)
        self.commit_selection_button.setStyleSheet(style.ACCENT_BUTTON_STYLE)
        self.commit_selection_button.clicked.connect(self.commit_selection)

        # ── Main layout ────────────────────────────────────────────────────
        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.main_layout.setSpacing(8)
        self.main_layout.setContentsMargins(12, 12, 12, 12)
        self.main_layout.addLayout(title_layout)
        self.main_layout.addWidget(subtitle)
        self.main_layout.addLayout(tree_body, stretch=1)

        if file_dropper:
            self.main_layout.addLayout(dd_row)

        if commit_selection:
            self.main_layout.addWidget(self.commit_selection_button)

        self.main_layout.addWidget(self.status_label)

        # ── Signals ────────────────────────────────────────────────────────
        self.add_shot_button.clicked.connect(self.add_shot)
        self.remove_shot_button.clicked.connect(self.remove_shot)
        self.add_project_button.clicked.connect(self.add_project)
        self.remove_project_button.clicked.connect(self.remove_project)
        self.add_shot_tags_button.clicked.connect(self.add_shot_tags)
        self.remove_shot_tags_button.clicked.connect(self.remove_shot_tags)
        self.save_button.clicked.connect(self.save)
        self.sort_by_dropdown.currentTextChanged.connect(self.refresh_tree)
        self.refresh_button.clicked.connect(lambda: self.refresh_tree(refresh_data=True))

        # ── Initial data load ──────────────────────────────────────────────
        self.sorted_data: Dict[Any, Any] = {}
        self.database = data_manager.ProjectDataManager()
        self.refresh_tree()

    # ── Helpers ──────────────────────────────────────────────────────────

    def _set_status(self, message: str, color: str = style.TEXT_SECONDARY):
        self.status_label.setStyleSheet(f"color: {color};")
        self.status_label.setText(message)

    # ── Tree management ───────────────────────────────────────────────────

    def refresh_tree(self, refresh_data=False) -> None:
        expansion_state = self.get_expansion_state()
        self.tree.clear()
        if refresh_data:
            self.database = data_manager.ProjectDataManager()
        tree_data = manager_utils.parse_data(self.database)
        sort_type = self.sort_by_dropdown.currentText()
        self.sorted_data = manager_utils.sort_data(tree_data, sort_type)
        self.populate_tree(self.sorted_data, self.tree.invisibleRootItem())
        self.format_tree()
        self.restore_expansion_state(expansion_state)

    def populate_tree(self, data, parent) -> None:
        for key, value in iter(data.items()):
            if isinstance(value, dict):
                item = QtWidgets.QTreeWidgetItem()
                item.setText(0, key)
                parent.addChild(item)
                self.populate_tree(value, item)
            else:
                item = QtWidgets.QTreeWidgetItem()
                item.setText(0, str(key))
                item.setText(1, str(value))
                parent.addChild(item)
                item.setFlags(item.flags() | QtCore.Qt.ItemIsEditable)  # type: ignore

    def format_tree(self) -> None:
        date_font = QtGui.QFont("Segoe UI", 10, QtGui.QFont.Bold, True)  # type: ignore
        path_font = QtGui.QFont("Consolas", 9)

        for i in range(self.tree.topLevelItemCount()):
            project_title = self.tree.topLevelItem(i)
            project_title.setForeground(0, self.project_color)
            project_title.setForeground(1, self.project_color)

        for i in range(self.tree.topLevelItemCount()):
            for j in range(self.tree.topLevelItem(i).childCount()):
                project_properties = self.tree.topLevelItem(i).child(j)
                project_properties.setForeground(0, self.primary_tree)
                project_properties.setForeground(1, self.secondary_tree)
                for k in range(self.tree.topLevelItem(i).child(j).childCount()):
                    shot_title = self.tree.topLevelItem(i).child(j).child(k)
                    shot_title.setForeground(0, self.shot_color)
                    shot_title.setForeground(1, self.shot_color)
                    for l in range(self.tree.topLevelItem(i).child(j).child(k).childCount()):
                        shot_properties = self.tree.topLevelItem(i).child(j).child(k).child(l)
                        shot_properties.setForeground(0, self.primary_tree)
                        shot_properties.setForeground(1, self.secondary_tree)

        for i in range(self.tree.topLevelItemCount()):
            project_title = self.tree.topLevelItem(i)
            project_name = self.tree.topLevelItem(i).text(0).replace(" ", "_").lower()
            project_obj = self.database.get_project(project_name)
            project_title.setText(1, str(project_obj.date))
            project_title.setText(2, str(project_obj.get_project_path()))
            project_title.setForeground(1, self.date_color)
            project_title.setFont(1, date_font)
            project_title.setForeground(2, self.date_color)
            project_title.setFont(2, path_font)

    # ── CRUD operations ───────────────────────────────────────────────────

    def add_shot(self) -> bool:
        if not self.tree.selectedItems():
            self._set_status("Select a project first.", style.ACCENT_YELLOW)
            return False
        database = data_manager.ProjectDataManager()
        selected_project = self.get_top_parent(self.tree.selectedItems()[0])
        try:
            project_name = selected_project.text(0).replace(" ", "_").lower()
            project_obj = database.get_project(project_name)
        except Exception as e:
            log.error(e)
            return False

        dialog = ShotDialog(self, project_obj)
        if not dialog.exec_():
            return False
        answers = dialog.get_answers()

        new_shot = shot.Shot(answers["Shot Name"],
                             project_obj,
                             frame_start=int(answers["Start Frame"]),
                             frame_end=int(answers["End Frame"]))

        database.add_shot(project_obj, new_shot)
        database.update_project(project_obj)
        self.refresh_tree(refresh_data=True)
        data_manager.ProjectDirectoryGenerator(shot_instance=new_shot, push_directories=True)
        self._set_status(f"Shot '{new_shot.name}' created.", style.ACCENT_GREEN)
        return True

    def remove_shot(self) -> bool:
        if not self.tree.selectedItems():
            self._set_status("Select a shot first.", style.ACCENT_YELLOW)
            return False
        database = data_manager.ProjectDataManager()
        selected_project = self.get_top_parent(self.tree.selectedItems()[0])
        selected_shot_name = self.tree.selectedItems()[0].text(0)
        try:
            project_name = selected_project.text(0).replace(" ", "_").lower()
            project_obj = database.get_project(project_name)
            shot_obj = project_obj.get_shot(selected_shot_name)
        except Exception as e:
            log.error(e)
            return False

        confirm = QtWidgets.QMessageBox.question(
            self, "Confirm", f"Remove shot '{selected_shot_name}'?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)  # type: ignore
        if confirm != QtWidgets.QMessageBox.Yes:  # type: ignore
            return False

        project_obj.remove_shot(shot_obj.name)
        database.update_project(project_obj)
        self.refresh_tree(refresh_data=True)
        self._set_status(f"Shot '{selected_shot_name}' removed.", style.TEXT_SECONDARY)
        return True

    def add_project(self) -> bool:
        dialog = ProjectDialog(self)
        if not dialog.exec_():
            return False
        answers = dialog.get_answers()
        project_name = answers.get("Project Name")
        project_description = answers.get("Project Description")
        if project_name:
            data_manager.ProjectDataManager().add_project(
                hpipe.core.project.Project(project_name, description=project_description))
        self.refresh_tree(refresh_data=True)
        self._set_status(f"Project '{project_name}' created.", style.ACCENT_GREEN)
        return True

    def remove_project(self) -> bool:
        if not self.tree.selectedItems():
            self._set_status("Select a project first.", style.ACCENT_YELLOW)
            return False
        database = data_manager.ProjectDataManager()
        selected_project = self.get_top_parent(self.tree.selectedItems()[0])
        project_name = selected_project.text(0).replace(" ", "_").lower()
        confirm = QtWidgets.QMessageBox.question(
            self, "Confirm", f"Remove project '{project_name}' and all its shots?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)  # type: ignore
        if confirm != QtWidgets.QMessageBox.Yes:  # type: ignore
            return False
        try:
            database.remove_project(database.get_project(project_name))
        except Exception as e:
            log.error(e)
            return False
        self.refresh_tree(refresh_data=True)
        self._set_status(f"Project '{project_name}' removed.", style.TEXT_SECONDARY)
        return True

    def commit_selection(self) -> bool:
        if not self.tree.selectedItems():
            return False
        selected_shot_item = self.tree.selectedItems()[0]
        shot_name = selected_shot_item.text(0)
        selected_project = self.get_top_parent(selected_shot_item)
        try:
            project_name = selected_project.text(0).replace(" ", "_").lower()
            project_from_db = self.database.get_project(project_name)
            shot_from_db = project_from_db.get_shot(shot_name)
        except Exception as e:
            log.error(e)
            return False
        log.debug(f"Selected shot: {shot_from_db}")
        return True

    # ── Drag & drop ───────────────────────────────────────────────────────

    def dragEnterEvent(self, event: QtGui.QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event: QtGui.QDropEvent):
        raise NotImplementedError

    # ── Tags (not yet implemented) ────────────────────────────────────────

    def add_shot_tags(self):
        raise NotImplementedError

    def remove_shot_tags(self):
        raise NotImplementedError

    # ── Save ──────────────────────────────────────────────────────────────

    def save(self):
        confirm = QtWidgets.QMessageBox.question(
            self, "Confirm Save", "Save all changes to the database?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)  # type: ignore
        if confirm != QtWidgets.QMessageBox.Yes:  # type: ignore
            return
        user_data = self.get_tree_contents(self.tree)
        database = data_manager.ProjectDataManager()
        updated_db_data = manager_utils.encode_data(user_data, database)
        database.data = updated_db_data
        database.save()
        self._set_status("Saved.", style.ACCENT_GREEN)

    # ── Tree traversal helpers ────────────────────────────────────────────

    def get_top_parent(self, item):
        parent = item.parent()
        if parent:
            return self.get_top_parent(parent)
        return item

    def get_tree_contents(self, tree, parent=None, result=None):
        # TODO: rethink the logic on this method
        if result is None:
            result = {}
        if parent is None:
            children = [tree.topLevelItem(i) for i in range(tree.topLevelItemCount())]
        else:
            children = [parent.child(i) for i in range(parent.childCount())]

        for child in children:
            item_key = child.text(0)
            item_value = child.text(1)
            is_top_level = parent is None
            # FIXME: need to also check if its the top level item to ignore stuff like the date and filepath
            if item_value and not is_top_level:
                result[item_key] = item_value
            else:
                result[item_key] = {}
                self.get_tree_contents(tree, child, result[item_key])
        return result

    def get_expansion_state(self) -> Tuple[List[str], List[str]]:
        expanded_projects = []
        expanded_shots = []
        for i in range(self.tree.topLevelItemCount()):
            if self.tree.topLevelItem(i).isExpanded():
                expanded_projects.append(self.tree.topLevelItem(i).text(0))
                for k in range(self.tree.topLevelItem(i).childCount()):
                    for j in range(self.tree.topLevelItem(i).child(k).childCount()):
                        if self.tree.topLevelItem(i).child(k).isExpanded():
                            expanded_shots.append(self.tree.topLevelItem(i).child(k).text(0))
                        for l in range(self.tree.topLevelItem(i).child(k).child(j).childCount()):
                            if self.tree.topLevelItem(i).child(k).child(j).isExpanded():
                                expanded_shots.append(
                                    self.tree.topLevelItem(i).child(k).child(j).text(0))
        return expanded_projects, expanded_shots

    def restore_expansion_state(self, expansion_state: Tuple[List[str], List[str]]) -> bool:
        for i in range(self.tree.topLevelItemCount()):
            if self.tree.topLevelItem(i).text(0) in expansion_state[0]:
                self.tree.topLevelItem(i).setExpanded(True)
                for j in range(self.tree.topLevelItem(i).childCount()):
                    if self.tree.topLevelItem(i).child(j).text(0) in expansion_state[1]:
                        self.tree.topLevelItem(i).child(j).setExpanded(True)
                    for k in range(self.tree.topLevelItem(i).child(j).childCount()):
                        if self.tree.topLevelItem(i).child(j).child(k).text(0) in expansion_state[1]:
                            self.tree.topLevelItem(i).child(j).child(k).setExpanded(True)
        return True
