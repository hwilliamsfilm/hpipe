"""
Pipe Manager GUI for managing projects, shots, and assets.
"""

from PySide6 import QtWidgets, QtCore, QtGui
from core import data_manager
import pipeConfig_widgets


class PipeConfig(QtWidgets.QWidget):
    """
    Project Overview Panel where I can see and edit all projects and shots. This is a project management tool
    and not a viewer.
    """
    def __init__(self, parent=None):
        super(PipeConfig, self).__init__(parent)

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

        # Spacer
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
        self.title_label = QtWidgets.QLabel('Pipe Config')
        self.icon = QtWidgets.QLabel()
        self.icon.setFixedSize(50, 50)
        self.icon_pixmap = QtGui.QPixmap('../../icons/film.png')
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
        self.tree.setItemDelegate(pipeConfig_widgets.EditableDelegate())
        self.tree.setItemDelegate(pipeConfig_widgets.EditableDelegate())

        self.tree_button_layout.addWidget(self.tree)
        self.tree_button_layout.addLayout(self.tree_button_layout)

        # configurations = ['Project', 'Shot', 'Asset', 'Sequence', 'Task', 'Software', 'User', 'Status', 'Version']
        # for config in configurations:
        #     self.tree.addTopLevelItem(self.tree.createItem(config))

        self.setLayout(self.main_layout)
        self.setWindowTitle('Pipe Config')
        self.resize(int(1920/1.5), int(1080/1.5))
        self.setWindowOpacity(0.99)
        self.setStyleSheet(self.window_stylesheet)
        self.database = data_manager.ProjectDataManager()

        self.setLayout(self.main_layout)

        # Watermark
        self.watermark_label = QtWidgets.QLabel('www.huntervfx.com | 2023')
        self.watermark_label.setFont(self.watermark_font)
        self.watermark_label.setStyleSheet("color: rgb(200, 200, 200)")
        self.watermark_label.setAlignment(QtCore.Qt.AlignBottom | QtCore.Qt.AlignRight)
        self.main_layout.addWidget(self.watermark_label)