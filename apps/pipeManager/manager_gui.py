"""
Pipe Manager GUI for managing projects, shots, and assets.
"""

from PySide6 import QtWidgets, QtCore, QtGui
from core import data_manager
import pipe_widgets


class ProjectOverview(QtWidgets.QWidget):
    """
    Project Overview Panel where I can see and edit all projects and shots. This is a project management tool
    and not a viewer.
    """
    def __init__(self, parent=None):
        super(ProjectOverview, self).__init__(parent)

        self.button_font = QtGui.QFont("Helvetica", 15, QtGui.QFont.Bold)
        self.tree_font = QtGui.QFont("Helvetica", 25)
        self.title_font = QtGui.QFont("Helvetica", 40, QtGui.QFont.Bold)
        self.title_font.setItalic(True)
        self.watermark_font = QtGui.QFont("Helvetica", 20, QtGui.QFont.Light)
        self.shot_color = QtGui.QColor(60, 110, 200)
        self.project_color = QtGui.QColor(200, 110, 60)
        self.button_stylesheet = "background-color: rgb(80, 90, 100); color: rgb(200, 200, 200)"
        self.window_stylesheet = "background-color: rgb(60, 60, 60); color: rgb(200, 200, 200);"
        self.row_height = 200
        self.alternating_color_stylesheet = "background-color: rgb(65, 65, 65); " \
                                            "alternate-background-color: rgb(55, 55, 55);"
        self.tree_stylesheet = "QTreeView::item { padding: 20px };"
        # set icon for window

        # create a spacer element
        self.spacer = QtWidgets.QLineEdit()
        self.spacer.setReadOnly(True)
        self.spacer.setVisible(True)
        self.spacer.setFrame(False)
        self.spacer.setStyleSheet(self.window_stylesheet)
        self.spacer.setFocusPolicy(QtCore.Qt.NoFocus)
        self.spacer_layout = QtWidgets.QVBoxLayout()
        self.spacer_layout.addWidget(self.spacer)

        # Create main title
        self.title_layout = QtWidgets.QHBoxLayout()
        self.title_label = QtWidgets.QLabel('Project Manager')
        self.icon = QtWidgets.QLabel()
        self.icon.setFixedSize(50, 50)
        self.icon_pixmap = QtGui.QPixmap('../../icons/germ.png')
        self.icon_pixmap = self.icon_pixmap.scaled(self.icon.size(), QtCore.Qt.KeepAspectRatio)
        self.icon.setPixmap(self.icon_pixmap)
        self.title_layout.addWidget(self.icon)
        self.title_label.setFont(self.title_font)
        self.title_label.setStyleSheet("color: rgb(200, 200, 200)")
        self.title_layout.addWidget(self.title_label)
        self.title_layout.addStretch()
        self.main_layout = QtWidgets.QVBoxLayout()
        self.tree_button_layout = QtWidgets.QHBoxLayout()
        self.setWindowIcon(QtGui.QIcon(self.icon_pixmap))

        self.main_layout.addLayout(self.title_layout)
        self.main_layout.addLayout(self.spacer_layout)
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
        self.tree.header().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
        self.tree.header().setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
        self.tree.header().setMinimumSectionSize(self.row_height)
        self.tree.setAlternatingRowColors(True)
        self.tree.header().setDefaultSectionSize(100)
        self.tree.setStyleSheet(self.alternating_color_stylesheet)
        self.tree.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.tree.setUniformRowHeights(True)
        self.tree.setItemDelegate(pipe_widgets.EditableDelegate())
        self.tree.setItemDelegate(pipe_widgets.EditableDelegate())

        self.tree_button_layout.addWidget(self.tree)

        # Create button layout
        self.button_layout = QtWidgets.QVBoxLayout()
        self.button_layout.setSpacing(10)
        self.button_layout.setAlignment(QtCore.Qt.AlignTop)
        self.tree_button_layout.addLayout(self.button_layout)

        # Add shot button
        self.add_shot_button = QtWidgets.QPushButton('Add Shot')
        self.add_shot_button.clicked.connect(self.add_shot)
        self.add_shot_button.setFixedHeight(40)
        self.add_shot_button.setFixedWidth(200)
        self.button_layout.addWidget(self.add_shot_button)
        self.add_shot_button.setFont(self.button_font)
        self.add_shot_button.setStyleSheet(self.button_stylesheet)

        # Add "add project" button
        self.add_project_button = QtWidgets.QPushButton('Add Project')
        self.add_project_button.clicked.connect(self.add_project)
        self.add_project_button.setFont(self.button_font)
        self.add_project_button.setFixedHeight(40)
        self.add_project_button.setFixedWidth(200)
        self.button_layout.addWidget(self.add_project_button)
        self.add_project_button.setStyleSheet(self.button_stylesheet)

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
        self.save_button.clicked.connect(self.save)
        self.save_button.setFixedHeight(40)
        self.save_button.setFixedWidth(200)
        self.save_button.setFont(self.button_font)
        self.button_layout.addWidget(self.save_button)
        self.save_button.setStyleSheet(self.button_stylesheet)

        # add tre view below main layout
        # TODO: Add drag and drop functionality
        self.drag_drop_button = QtWidgets.QPushButton("Drag and drop here to ingest files.")
        self.drag_drop_button.setStyleSheet('color: rgb(200, 200, 200)')
        self.drag_drop_button.setFlat(True)
        self.drag_drop_button.setStyleSheet("border: 2px solid rgb(30, 30, 30);")
        self.drag_drop_button.setFixedHeight(100)
        self.drag_drop_button.setFont(QtGui.QFont("Helvetica", 15, QtGui.QFont.Light))
        self.drag_drop_button.setAcceptDrops(True)
        self.main_layout.addWidget(self.drag_drop_button)

        self.setLayout(self.main_layout)

        self.watermark_label = QtWidgets.QLabel('www.huntervfx.com | 2023')
        self.watermark_label.setFont(self.watermark_font)
        self.watermark_label.setStyleSheet("color: rgb(200, 200, 200)")
        self.watermark_label.setAlignment(QtCore.Qt.AlignBottom | QtCore.Qt.AlignRight)
        self.main_layout.addWidget(self.watermark_label)

        # Refresh
        self.refresh_tree()

    def refresh_tree(self) -> None:
        """
        Refresh the tree widget. This is called when the window is first opened and when the user clicks the
        "refresh" button.
        :return: True if successful.
        """
        expansion_state = self.get_expansion_state()
        self.tree.clear()
        self.populate_tree(self.database.data, self.tree.invisibleRootItem())
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
                item.setFlags(item.flags() | QtCore.Qt.ItemIsEditable)

    def format_tree(self) -> None:
        """
        Format the tree widget. This is called when the window is first opened and when the user clicks the
        "refresh" button.
        """

        # make project titles red
        for i in range(self.tree.topLevelItemCount()):
            self.tree.topLevelItem(i).setForeground(0, self.project_color)
            self.tree.topLevelItem(i).setForeground(1, self.project_color)

        # make all shots blue
        for i in range(self.tree.topLevelItemCount()):
            for j in range(self.tree.topLevelItem(i).childCount()):
                for k in range(self.tree.topLevelItem(i).child(j).childCount()):
                    self.tree.topLevelItem(i).child(j).child(k).setForeground(0, self.shot_color)
                    self.tree.topLevelItem(i).child(j).child(k).setForeground(1, self.shot_color)

                    # TODO: move this to a separate function. It adds shot tags to the tree widget.
                    # project_name = self.tree.topLevelItem(i).text(0)
                    # shot = self.tree.topLevelItem(i).child(j).child(k).text(0)
                    # shot_tags = self.database.get_project(project_name).get_shot(shot).get_tags()
                    # if shot_tags is not None and shot_tags is not ['']:
                    #     button = pipe_widgets.MultipleTagWidget(shot_tags)
                    #     self.tree.setItemWidget(self.tree.topLevelItem(i).child(j).child(k), 3, button)

    def add_shot(self) -> bool:
        """
        Add a shot to the project/database and tree widget.
        :return: True if successful.
        """
        raise NotImplementedError

    def add_project(self) -> bool:
        """
        Add a project to the database and tree widget.
        :return: True if successful.
        """

    def remove_project(self) -> bool:
        """
        Remove a project from the database and tree widget.
        :return: True if successful.
        """
        raise NotImplementedError

    def tree_contents(self):
        """
        Get the contents of the tree
        :return:
        """
        raise NotImplementedError

    def get_children(self, item):
        """
        Get the children of the given item
        :param item:
        :return:
        """
        raise NotImplementedError

    def save(self):
        """
        Save the data to the database
        :return:
        """
        raise NotImplementedError

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

    def get_expansion_state(self) -> tuple[list[str], list[str]]:
        """
        Get the expansion state of the tree
        :return: A tuple containing the expanded projects and shots
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

        return expanded_projects, expanded_shots

    def restore_expansion_state(self, expansion_state: tuple[list[str], list[str]]) -> bool:
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

        return True
