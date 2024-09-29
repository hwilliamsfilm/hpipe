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
from hpipe.core.hutils import logger
from typing import *

log = logger.setup_logger()
log.debug("manager_gui.py loaded")


class ProjectDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Create Project")

        prompts = ["Project Name", "Project Description"]
        self.layout = QtWidgets.QVBoxLayout()

        for prompt in prompts:
            prompt_layout = QtWidgets.QHBoxLayout()
            label = QtWidgets.QLabel(prompt, self)
            q_input = QtWidgets.QLineEdit(self)
            prompt_layout.addWidget(label)
            prompt_layout.addWidget(q_input)
            self.layout.addLayout(prompt_layout)

        self.create_button = QtWidgets.QPushButton("Create", self)
        self.create_button.clicked.connect(self.accept)

        self.layout.addWidget(self.create_button)

        self.setLayout(self.layout)

    def get_answers(self) -> dict:
        """
        Returns a dictionary of the answers from the dialog.
        """
        answers = {}
        for i in range(self.layout.count()):  # type: ignore
            item = self.layout.itemAt(i)  # type: ignore
            if isinstance(item, QtWidgets.QHBoxLayout):
                dialogue_label = item.itemAt(0).widget().text()  # type: ignore
                dialogue_input = item.itemAt(1).widget().text()  # type: ignore
                answers[dialogue_label] = dialogue_input
        return answers


class ShotDialog(QtWidgets.QDialog):
    def __init__(self, parent = None, project_for_shot: Union['project.Project', Any] = None):
        super().__init__(parent)

        self.setWindowTitle(f"Create Shot in {project_for_shot.name}")

        prompts = ["Shot Name", "Start Frame", "End Frame"]
        self.layout = QtWidgets.QVBoxLayout()  # type: ignore

        for prompt in prompts:
            prompt_layout = QtWidgets.QHBoxLayout()
            label = QtWidgets.QLabel(prompt, self)
            q_input = QtWidgets.QLineEdit(self)
            prompt_layout.addWidget(label)
            prompt_layout.addWidget(q_input)
            self.layout.addLayout(prompt_layout)  # type: ignore

        self.create_button = QtWidgets.QPushButton("Create", self)
        self.create_button.clicked.connect(self.accept)

        self.layout.addWidget(self.create_button)  # type: ignore

        self.setLayout(self.layout)  # type: ignore

    def get_answers(self) -> dict:
        """
        Returns a dictionary of the answers from the dialog.
        """
        answers = {}
        for i in range(self.layout.count()):  # type: ignore
            item = self.layout.itemAt(i)  # type: ignore
            if isinstance(item, QtWidgets.QHBoxLayout):
                dialogue_label = item.itemAt(0).widget().text()  # type: ignore
                dialogue_input = item.itemAt(1).widget().text()  # type: ignore
                answers[dialogue_label] = dialogue_input
        return answers


class ProjectOverview(QtWidgets.QWidget):
    """
    Project Overview Panel where I can see and edit all projects and shots. This is a project management tool
    and not a viewer.
    """
    def __init__(self,
                 parent=None,
                 font_scale: float = 1.0,
                 file_dropper: bool = True,
                 sidebar: bool = True,
                 commit_selection: bool = False):

        super(ProjectOverview, self).__init__(parent)

        small_font = int(15 * font_scale)
        large_font = int(40 * font_scale)
        medium_font = int(25 * font_scale)
        self.button_font = QtGui.QFont("Helvetica", small_font, QtGui.QFont.Bold)  # type: ignore
        self.dropdown_font = QtGui.QFont("Helvetica", small_font, QtGui.QFont.Light)  # type: ignore
        self.tree_font = QtGui.QFont("Helvetica",medium_font, QtGui.QFont.Bold)  # type: ignore
        self.title_font = QtGui.QFont("Helvetica", large_font, QtGui.QFont.Bold)  # type: ignore
        self.title_font.setItalic(True)
        self.subtitle_font = QtGui.QFont("Helvetica", small_font, QtGui.QFont.Light)  # type: ignore
        self.subtitle_font.setItalic(True)
        self.watermark_font = QtGui.QFont("Helvetica", medium_font, QtGui.QFont.Light)  # type: ignore
        self.date_font = QtGui.QFont("Helvetica", medium_font, QtGui.QFont.Bold, italic=True)  # type: ignore
        self.filepath_font = QtGui.QFont("Helvetica", small_font, QtGui.QFont.Bold, italic=True)  # type: ignore
        self.drag_drop_font = QtGui.QFont("Helvetica", small_font, QtGui.QFont.Light)  # type: ignore
        self.tree_color = QtGui.QColor(100, 100, 100)
        self.shot_color = QtGui.QColor(60, 110, 200)
        self.project_color = QtGui.QColor(200, 110, 60)
        self.date_color = QtGui.QColor(100, 100, 100)
        self.primary_tree = QtGui.QColor(180, 180, 180)
        self.secondary_tree = QtGui.QColor(100, 100, 100)
        self.button_stylesheet = "background-color: rgb(80, 90, 100); color: rgb(200, 200, 200)"
        self.window_stylesheet = "background-color: rgb(60, 60, 60); color: rgb(200, 200, 200);"
        self.row_height = 200
        self.alternating_color_stylesheet = "background-color: rgb(65, 65, 65); " \
                                            "alternate-background-color: rgb(55, 55, 55);"
        self.tree_stylesheet = "QTreeView::item { padding: 20px };"

        # create a spacer element
        self.spacer = QtWidgets.QLineEdit()
        self.spacer.setReadOnly(True)
        # self.spacer.setVisible(True)
        self.spacer.setFrame(False)
        self.spacer.setStyleSheet(self.window_stylesheet)
        self.spacer.setFocusPolicy(QtCore.Qt.NoFocus)  # type: ignore
        self.spacer_layout = QtWidgets.QVBoxLayout()
        self.spacer_layout.addWidget(self.spacer)

        # add "sort by" dropdown
        self.sort_by_layout = QtWidgets.QHBoxLayout()
        self.sort_by_layout.setAlignment(QtCore.Qt.AlignRight)  # type: ignore
        self.sort_by_label = QtWidgets.QLabel('Sort By:')
        self.sort_by_label.setFont(self.dropdown_font)
        self.sort_by_label.setStyleSheet(self.window_stylesheet)
        self.sort_by_layout.addWidget(self.sort_by_label)
        self.sort_by_dropdown = QtWidgets.QComboBox()
        self.sort_by_dropdown.setStyleSheet("QComboBox { combobox-popup: 0; }")
        self.sort_by_dropdown.addItems(manager_utils.Constants().SORTING_TYPES)
        self.sort_by_dropdown.setFont(self.dropdown_font)
        self.sort_by_layout.addWidget(self.sort_by_dropdown)

        # Add "Refresh" button
        self.refresh_button = QtWidgets.QPushButton()
        self.refresh_pixmap = QtGui.QPixmap('../../icons/cupcake.png')
        self.refresh_button.setFixedHeight(40)
        self.refresh_button.setFixedWidth(40)
        self.refresh_button.setFlat(True)
        self.refresh_button.setCursor(QtCore.Qt.PointingHandCursor)  # type: ignore
        self.refresh_button.setToolTip('Refresh')
        self.refresh_button.setIconSize(QtCore.QSize(40, 40))
        self.refresh_button.setIcon(QtGui.QIcon(self.refresh_pixmap))
        self.sort_by_layout.addWidget(self.refresh_button)
        self.refresh_button.setStyleSheet(self.button_stylesheet)

        # Create main title
        self.title_layout = QtWidgets.QHBoxLayout()
        self.title_label = QtWidgets.QLabel('Project Manager')
        self.icon = QtWidgets.QLabel()
        self.icon.setFixedSize(50, 50)
        self.icon_pixmap = QtGui.QPixmap('../../icons/germ.png')
        self.icon_pixmap = self.icon_pixmap.scaled(self.icon.size(), QtCore.Qt.KeepAspectRatio)  # type: ignore
        self.icon.setPixmap(self.icon_pixmap)
        self.title_layout.addWidget(self.icon)
        self.title_label.setFont(self.title_font)
        self.title_label.setStyleSheet("color: rgb(200, 200, 200)")
        self.title_layout.addWidget(self.title_label)
        self.title_layout.addStretch()
        self.main_layout = QtWidgets.QVBoxLayout()
        self.tree_button_layout = QtWidgets.QHBoxLayout()
        self.setWindowIcon(QtGui.QIcon(self.icon_pixmap))

        self.subtitle = QtWidgets.QLabel()
        self.subtitle.setText("'Chaos is just order waiting to be discovered.'")
        self.subtitle.setFont(self.subtitle_font)

        self.main_layout.addLayout(self.title_layout)
        self.main_layout.addWidget(self.subtitle)
        self.main_layout.addLayout(self.tree_button_layout)

        self.setLayout(self.main_layout)
        self.setWindowTitle('Project Manager')
        self.resize(int(1920/1.5), int(1080/1.5))
        self.setWindowOpacity(0.99)
        self.setStyleSheet(self.window_stylesheet)
        self.database = data_manager.ProjectDataManager()

        # Create tree widget
        self.tree = QtWidgets.QTreeWidget()
        self.tree.setColumnCount(4)
        self.tree.setHeaderHidden(True)
        self.tree.setFont(self.tree_font)
        self.tree.header().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)  # type: ignore
        self.tree.header().setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)  # type: ignore
        self.tree.header().setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeToContents)  # type: ignore
        self.tree.header().setMinimumSectionSize(self.row_height)
        self.tree.setAlternatingRowColors(True)
        self.tree.header().setDefaultSectionSize(100)
        self.tree.setStyleSheet(self.alternating_color_stylesheet)
        self.tree.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)  # type: ignore
        self.tree.setUniformRowHeights(True)
        self.tree.setItemDelegate(pipe_widgets.EditableDelegate())
        self.tree.setItemDelegate(pipe_widgets.EditableDelegate())
        self.tree_header_layout = QtWidgets.QVBoxLayout()

        self.tree_header_layout.addLayout(self.sort_by_layout)
        self.tree_header_layout.addWidget(self.tree)

        self.tree_button_layout.addLayout(self.tree_header_layout)

        # Create button layout
        self.button_layout = QtWidgets.QVBoxLayout()
        self.button_layout.setSpacing(10)
        self.button_layout.setAlignment(QtCore.Qt.AlignTop)  # type: ignore
        if sidebar:
            self.tree_button_layout.addLayout(self.button_layout)

        # Add shot button
        self.add_shot_button = QtWidgets.QPushButton('Add Shot')
        self.add_shot_button.clicked.connect(self.add_shot)
        self.add_shot_button.setFixedHeight(40)
        self.add_shot_button.setFixedWidth(200)
        self.button_layout.addWidget(self.add_shot_button)
        self.add_shot_button.setFont(self.button_font)
        self.add_shot_button.setStyleSheet(self.button_stylesheet)

        # Remove shot button
        self.remove_shot_button = QtWidgets.QPushButton('Remove Shot')
        self.remove_shot_button.clicked.connect(self.remove_shot)
        self.remove_shot_button.setFixedHeight(40)
        self.remove_shot_button.setFixedWidth(200)
        self.button_layout.addWidget(self.remove_shot_button)
        self.remove_shot_button.setFont(self.button_font)
        self.remove_shot_button.setStyleSheet(self.button_stylesheet)

        # Add "add project" button
        self.add_project_button = QtWidgets.QPushButton('Add Project')
        self.add_project_button.clicked.connect(self.add_project)
        self.add_project_button.setFont(self.button_font)
        self.add_project_button.setFixedHeight(40)
        self.add_project_button.setFixedWidth(200)
        self.button_layout.addWidget(self.add_project_button)
        self.add_project_button.setStyleSheet(self.button_stylesheet)

        # Add "remove project" button
        self.remove_project_button = QtWidgets.QPushButton('Remove Project')
        self.remove_project_button.clicked.connect(self.remove_project)
        self.remove_project_button.setFont(self.button_font)
        self.remove_project_button.setFixedHeight(40)
        self.remove_project_button.setFixedWidth(200)
        self.button_layout.addWidget(self.remove_project_button)
        self.remove_project_button.setStyleSheet(self.button_stylesheet)

        # Add "shot tags" button
        self.add_shot_tags_button = QtWidgets.QPushButton('Add Shot Tags')
        self.add_shot_tags_button.clicked.connect(self.add_shot_tags)
        self.add_shot_tags_button.setFixedHeight(40)
        self.add_shot_tags_button.setFixedWidth(200)
        self.add_shot_tags_button.setFont(self.button_font)
        self.button_layout.addWidget(self.add_shot_tags_button)
        self.add_shot_tags_button.setStyleSheet(self.button_stylesheet)

        # Add "remove shot tags" button
        self.remove_shot_tags_button = QtWidgets.QPushButton('Remove Shot Tags')
        self.remove_shot_tags_button.clicked.connect(self.remove_shot_tags)
        self.remove_shot_tags_button.setFixedHeight(40)
        self.remove_shot_tags_button.setFixedWidth(200)
        self.remove_shot_tags_button.setFont(self.button_font)
        self.button_layout.addWidget(self.remove_shot_tags_button)
        self.remove_shot_tags_button.setStyleSheet(self.button_stylesheet)

        # Add "save" button
        self.save_button = QtWidgets.QPushButton('Save')
        self.save_button.setFixedHeight(40)
        self.save_button.setFixedWidth(200)
        self.save_button.setFont(self.button_font)
        self.button_layout.addWidget(self.save_button)
        self.save_button.setStyleSheet(self.button_stylesheet)

        # Add "Drag and Drop" button
        self.drag_drop_layout = QtWidgets.QHBoxLayout()
        self.drag_drop_button = QtWidgets.QPushButton("Drag and drop here to ingest files.")
        self.drag_drop_button.setStyleSheet('color: rgb(200, 200, 200)')
        self.drag_drop_button.setFlat(True)
        self.drag_drop_button.setStyleSheet("border: 2px solid rgb(30, 30, 30);")
        self.drag_drop_button.setFixedHeight(100)
        self.drag_drop_button.setFont(self.drag_drop_font)
        self.drag_drop_button.setAcceptDrops(True)
        self.drag_drop_button.dragEnterEvent = self.dragEnterEvent  # type: ignore
        self.drag_drop_button.dropEvent = self.dropEvent  # type: ignore
        self.drag_drop_layout.addWidget(self.drag_drop_button)
        self.drag_drop_combo_layout = QtWidgets.QVBoxLayout()
        self.drag_drop_combo = QtWidgets.QComboBox()
        self.drag_drop_combo.addItems(manager_utils.Constants().INGEST_LOCATIONS)
        self.drag_drop_combo.setFixedHeight(40)
        self.drag_drop_combo.setFixedWidth(200)
        self.loading_bar = QtWidgets.QProgressBar()
        self.loading_bar.setFixedHeight(40)
        self.loading_bar.setFixedWidth(200)
        self.drag_drop_combo_layout.addWidget(self.drag_drop_combo)
        self.drag_drop_combo_layout.addWidget(self.loading_bar)
        self.drag_drop_layout.addLayout(self.drag_drop_combo_layout)

        if file_dropper:
            self.main_layout.addLayout(self.drag_drop_layout)

        self.commit_selection_layout = QtWidgets.QHBoxLayout()
        self.commit_selection_button = QtWidgets.QPushButton("Select Shot")
        self.commit_selection_button.setFixedHeight(40)
        self.commit_selection_layout.addWidget(self.commit_selection_button)
        self.commit_selection_button.clicked.connect(self.commit_selection)

        if commit_selection:
            self.main_layout.addLayout(self.commit_selection_layout)

        self.setLayout(self.main_layout)

        self.watermark_label = QtWidgets.QLabel('2024')
        self.watermark_label.setFont(self.watermark_font)
        self.watermark_label.setStyleSheet("color: rgb(200, 200, 200)")
        self.watermark_label.setAlignment(QtCore.Qt.AlignBottom | QtCore.Qt.AlignRight)  # type: ignore
        self.main_layout.addWidget(self.watermark_label)

        # Connect signals
        self.sort_by_dropdown.currentTextChanged.connect(self.refresh_tree)
        self.refresh_button.clicked.connect(lambda: self.refresh_tree(refresh_data=True))
        self.save_button.clicked.connect(self.save)

        # Refresh
        self.sorted_data: Dict[Any, Any] = {}
        self.refresh_tree()

    def refresh_tree(self, refresh_data=False) -> None:
        """
        Refresh the tree widget. This is called when the window is first opened and when the user clicks the
        "refresh" button.
        :return: True if successful.
        """
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
        """
        Populate the tree widget with the data from the database.
        :param data: The data to populate the tree with.
        :param parent: The parent item.
        """
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
        """
        Format the tree widget. This is called when the window is first opened and when the user clicks the
        "refresh" button.
        """

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

        # add date to the second column next to the project name
        for i in range(self.tree.topLevelItemCount()):
            project_title = self.tree.topLevelItem(i)
            project_name = self.tree.topLevelItem(i).text(0).replace(" ", "_").lower()
            project_date = self.database.get_project(project_name).date
            project_path = self.database.get_project(project_name).get_project_path()
            project_title.setText(1, str(project_date))
            project_title.setText(2, str(project_path))
            project_title.setForeground(1, self.date_color)
            project_title.setFont(1, self.date_font)
            project_title.setForeground(2, self.date_color)
            project_title.setFont(2, self.filepath_font)

    def add_shot(self) -> bool:
        """
        Add a shot to the project/database and tree widget.
        :return: True if successful.
        """
        database = data_manager.ProjectDataManager()
        selected_project = self.get_top_parent(self.tree.selectedItems()[0])
        if not self.tree.selectedItems():
            return False
        try:
            project_name = selected_project.text(0).replace(" ", "_").lower()
            project = database.get_project(project_name)
        except Exception as e:
            log.error(e)
            return False

        dialog = ShotDialog(self, project)
        answers: Dict[str, str] = {}
        if dialog.exec_():
            answers = dialog.get_answers()

        new_shot = shot.Shot(answers.get('Shot Name'),
                             project,
                             frame_start=int(answers.get('Start Frame')),
                             frame_end=int(answers.get('End Frame')))

        database.add_shot(project, new_shot)
        log.debug(answers)
        database.update_project(project)
        self.refresh_tree(refresh_data=True)
        data_manager.ProjectDirectoryGenerator(shot_instance=new_shot, push_directories=True)
        return True

    def remove_shot(self) -> bool:
        """
        Remove a shot from the project/database and tree widget.
        :return: True if successful.
        """
        database = data_manager.ProjectDataManager()
        selected_project = self.get_top_parent(self.tree.selectedItems()[0])
        selected_shot = self.tree.selectedItems()[0].text(0)

        if not selected_project or not selected_shot:
            return False

        try:
            project_name = selected_project.text(0).replace(" ", "_").lower()
            project = database.get_project(project_name)
            shot = project.get_shot(selected_shot)
        except Exception as e:
            log.error(e)
            return False

        project.remove_shot(shot.name)
        database.update_project(project)
        self.refresh_tree(refresh_data=True)
        return True

    def add_project(self) -> bool:
        """
        Add a project to the database and tree widget.
        :return: True if successful.
        """
        dialog = ProjectDialog(self)
        answers = {}
        if dialog.exec_():
            answers = dialog.get_answers()

        log.debug(answers)

        project_name = answers.get('Project Name')
        project_description = answers.get("Project Description")

        if project_name and project_description:
            data_manager.ProjectDataManager().add_project(
                hpipe.core.project.Project(project_name, description=project_description))

        self.refresh_tree(refresh_data=True)

        return True

    def dragEnterEvent(self, event: QtGui.QDragEnterEvent):
        """
        Drag enter event.
        :param event: The event.
        """
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event: QtGui.QDropEvent):
        """
        Drop event.
        :param event: The event.
        """
        # filepath = ''
        # target_location = self.drag_drop_combo.currentText()
        #
        # if event.mimeData().hasUrls():
        #     for url in event.mimeData().urls():
        #         filepath = url.toLocalFile()
        # else:
        #     event.ignore()
        #
        # if filepath == '':
        #     return False
        #
        # try:
        #     selected_project = self.get_top_parent(self.tree.selectedItems()[0])
        # except IndexError:
        #     selected_project = None
        #
        # project_name = selected_project.text(0).replace(" ", "_").lower()
        # selected_shot = self.tree.selectedItems()[0]
        # shot_name = selected_shot.text(0).replace(" ", "_")
        # project_list = [proj.name for proj in self.database.get_projects()]
        #
        # if project_name in project_list:
        #     project_object = self.database.get_project(project_name)
        #     shot_list = [shot.name for shot in project_object.get_shots()]
        #     if shot_name in shot_list:
        #         shot_object = project_object.get_shot(shot_name)
        #         manager_utils.ingest_file(filepath, target_location, project_object, shot_object)
        #         return True
        #     # its a valid project and should at least be added here
        #     return True
        # else:
        #     # its not a valid project or shot, so lets add it globally
        #     return True
        raise NotImplementedError

    def remove_project(self) -> bool:
        """
        Remove a project from the database and tree widget.
        :return: True if successful.
        """
        database = data_manager.ProjectDataManager()
        if not self.tree.selectedItems():
            return False
        selected_project = self.get_top_parent(self.tree.selectedItems()[0])
        try:
            project_name = selected_project.text(0).replace(" ", "_").lower()
            database.remove_project(database.get_project(project_name))
        except Exception as e:
            log.error(e)
            return False
        self.refresh_tree(refresh_data=True)
        return True

    def commit_selection(self) -> bool:
        """
        Return the selected shot and close the window.
        :return: True if successful.
        """
        selected_shot = self.tree.selectedItems()[0]
        shot_name = selected_shot.text(0)
        selected_project = self.get_top_parent(selected_shot)
        try:
            project_name = selected_project.text(0).replace(" ", "_").lower()
            project_from_db = self.database.get_project(project_name)
            shot_from_db = project_from_db.get_shot(shot_name)
        except Exception as e:
            log.error(e)
            return False

        # self.close()
        log.debug(f"Selected shot: {shot_from_db}")
        log.debug(f"Selected project: {project_from_db}")
        return True

    def get_top_parent(self, item):
        """
        Get the top parent of an item.
        :param item: The item to get the top parent of.
        :return: The top parent of the item.
        """
        parent = item.parent()
        if parent:
            return self.get_top_parent(parent)
        else:
            return item

    def get_tree_contents(self, tree, parent=None, result=None):
        # TODO: rethink the logic on this method
        """
        Recursively converts the data from a QTreeWidget into a dictionary.
        :param tree: QTreeWidget to extract data from
        :param parent: Parent QTreeWidgetItem (used in recursion)
        :param result: Dictionary to store the extracted data (used in recursion)
        :return: Dictionary containing the QTreeWidget data
        """
        if result is None:
            result = {}
        if parent is None:
            children = [tree.topLevelItem(i) for i in range(tree.topLevelItemCount())]
        else:
            children = [parent.child(i) for i in range(parent.childCount())]

        for child in children:
            item_key = child.text(0)
            item_value = child.text(1)

            if parent is not None:
                item_key = f"{item_key}"

            # FIXME: need to also check if its the top level item to ignore stuff like the date and filepath
            is_top_level = False
            if parent is None:
                is_top_level = True

            if item_value and not is_top_level:
                result[item_key] = item_value
            else:
                result[item_key] = {}
                self.get_tree_contents(tree, child, result[item_key])
        return result

    def get_children(self, item):
        """
        Get the children of the given item
        :param item:
        :return:
        """
        raise NotImplementedError

    def save(self):
        # TODO: This is pretty un-elegant, should probably have some QC before saving or pop up, "are you sure" etc
        """
        Save the data to the database
        :return:
        """
        user_data = self.get_tree_contents(self.tree)
        database = data_manager.ProjectDataManager()
        updated_db_data = manager_utils.encode_data(user_data, database)
        database.data = updated_db_data
        database.save()

    def add_shot_tags(self):
        """
        Add tags to a shot
        :return:
        """
        raise NotImplementedError

    def remove_shot_tags(self):
        """
        Remove tags from a shot
        :return:
        """
        raise NotImplementedError

    def get_expansion_state(self) -> Tuple[List[str], List[str]]:
        """
        Get the expansion state of the tree
        :return: A Tuple containing the expanded projects and shots
        """
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
                                expanded_shots.append(self.tree.topLevelItem(i).child(k).child(j).text(0))

        return expanded_projects, expanded_shots

    def restore_expansion_state(self, expansion_state: Tuple[List[str], List[str]]) -> bool:
        """
        Restore the expansion state of the tree
        :param expansion_state: The expansion state to restore
        :return: True if successful
        """
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
