"""
Pipe Manager GUI for viewing outputs, comps, and renders.
"""

import sys
try:
    import hou
    from PySide2 import QtWidgets, QtCore, QtGui
except Exception as e:
    print(f'hou not found, not running in houdini: {e}')
    from PySide6 import QtWidgets, QtCore, QtGui

from core import data_manager, project, shot
from apps.pipeDisplay import output_widgets, output_utils
from core.hutils import logger
from typing import *
from assets import reviewable
import time

log = logger.setup_logger()
log.debug("manager_gui.py loaded")


class ThumbnailLoader(QtCore.QThread):
    """
    Thread for loading thumbnails in the background based on the directories in the project.
    """
    thumbnail_loaded = QtCore.Signal(QtGui.QPixmap, int)

    def __init__(self, reviewable_list: List[reviewable.Reviewable]):
        super().__init__()
        self.reviewable_list = reviewable_list

        # need to keep track of the thread's running state so we can prevent the thread from emitting signals after
        # it's already been stopped
        self._running = True

    def run(self):
        """
        Load thumbnails for each reviewable in the project. Emit a signal when each thumbnail is loaded with the
        index of the reviewable in the list.
        """
        for index, reviewable_instance in enumerate(self.reviewable_list):
            image = reviewable_instance.get_thumbnail_image()
            if image:
                thumbnail = QtGui.QPixmap(image.system_path())
            else:
                thumbnail = QtGui.QPixmap(output_utils.Constants.TEMP_IMAGE.system_path())
            if self._running:
                self.thumbnail_loaded.emit(thumbnail, index)

            # sleep for a bit so we don't overload the main thread sending signals back
            time.sleep(0.001)

    def stop(self):
        self._running = False
        self.requestInterruption()
        self.wait()


class OutputViewer(QtWidgets.QDialog):
    """
    Project Overview Panel where I can see and edit all projects and shots. This is a project management tool
    and not a viewer.
    """
    def __init__(self, parent=None,
                 font_scale: float = 1.0,
                 start_project: str = output_utils.Constants.START_PROJECT,
                 show_side_bar: bool = True,
                 start_type="Assets",
                 position: tuple = None,
                 size: tuple = None,
                 icon_size: int = None):
        super(OutputViewer, self).__init__(parent)

        self.return_value = {}

        self.isDialog = abs(show_side_bar-1)

        small_font = int(15 * font_scale)
        large_font = int(40 * font_scale)
        medium_font = int(25 * font_scale)
        self.button_font = QtGui.QFont("Arial", small_font)
        self.button_styleSheet = "background-color: #2d2d2d; color: #ffffff;"
        self.title_font = QtGui.QFont("Helvetica", large_font, QtGui.QFont.Bold)  # type: ignore
        self.title_font.setItalic(True)
        self.subtitle_font = QtGui.QFont("Helvetica", small_font, QtGui.QFont.Light)  # type: ignore
        self.subtitle_font.setItalic(True)
        self.watermark_font = QtGui.QFont("Helvetica", medium_font, QtGui.QFont.Light)  # type: ignore

        self.setWindowTitle('Output Viewer')
        self.database = data_manager.ProjectDataManager()
        self.loader_thread: Optional[ThumbnailLoader] = ThumbnailLoader([])

        # make title bar
        self.title_layout = QtWidgets.QHBoxLayout()
        self.title_label = QtWidgets.QLabel('Pipe Output Viewer')
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
        self.setWindowIcon(QtGui.QIcon(self.icon_pixmap))

        self.body_layout = QtWidgets.QHBoxLayout()
        self.stackedLayout = QtWidgets.QStackedLayout()

        self.flow_layout = output_widgets.FlowLayout()
        self.thumbnail_layout = QtWidgets.QScrollArea()
        container = QtWidgets.QWidget()
        container.setLayout(self.flow_layout)
        self.thumbnail_layout.setWidget(container)
        self.thumbnail_layout.setWidgetResizable(True)
        self.thumbnail_layout.setMinimumWidth(20)
        self.thumbnail_layout.setMaximumWidth(5000)

        self.thumbnail_layout.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)  # type: ignore

        self.context_menu = QtWidgets.QMenu(self)
        self.open_action = self.context_menu.addAction("Open In Explorer")
        self.open_in_rv_action = self.context_menu.addAction("Open In RV")
        self.move_to_delivery_action = self.context_menu.addAction("Move To Delivery")

        self.list_layout = QtWidgets.QTableWidget()
        self.list_layout.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)  # type: ignore
        self.list_layout.verticalHeader().setVisible(False)
        self.list_layout.setColumnCount(1)
        self.list_layout.setAlternatingRowColors(True)
        self.list_layout.horizontalHeader().setVisible(False)
        self.list_layout.setStyleSheet("alternate-background-color: #2d2d2d; background-color: #1d1d1d; color: #ffffff;")
        self.list_layout.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)  # type: ignore

        self.show_selection = QtWidgets.QComboBox()
        self.seq_selection = QtWidgets.QComboBox()
        self.shot_selection = QtWidgets.QComboBox()
        self.directory_type = QtWidgets.QComboBox()

        self.sequence_toggle = QtWidgets.QCheckBox("Browse by Sequence")
        self.filter = QtWidgets.QLineEdit()
        self.filter.setPlaceholderText("Filter")
        self.icon_view = QtWidgets.QCheckBox("Icon View")
        self.latest_version = QtWidgets.QCheckBox("Latest Version Only")

        self.size_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)  # type: ignore
        self.size_slider.setMinimum(50)
        self.size_slider.setMaximum(400)
        if not icon_size:
            icon_size = 100
        self.size_slider.setValue(icon_size)
        self.size_slider.setTickInterval(10)
        self.size_slider.setTickPosition(QtWidgets.QSlider.TicksBelow)  # type: ignore

        self.loading_bar = QtWidgets.QProgressBar()
        self.loading_bar.setRange(0, 100)
        self.loading_bar.setTextVisible(False)

        self.loading_bar.setValue(100)

        button_layout = QtWidgets.QVBoxLayout()
        button_layout.setAlignment(QtCore.Qt.AlignTop)  # type: ignore
        # button_layout.addWidget(self.filter)
        # button_layout.addWidget(output_widgets.QHLine())  # type: ignore
        # button_layout.addWidget(self.icon_view)
        # button_layout.addWidget(output_widgets.QHLine())  # type: ignore
        button_layout.addWidget(self.directory_type)
        button_layout.addWidget(output_widgets.QHLine())  # type: ignore
        button_layout.addWidget(self.show_selection)
        button_layout.addWidget(self.shot_selection)
        button_layout.addWidget(output_widgets.QHLine())  # type: ignore
        button_layout.addWidget(self.sequence_toggle)
        button_layout.addWidget(self.latest_version)
        button_layout.addWidget(output_widgets.QHLine())  # type: ignore
        button_layout.addWidget(self.size_slider)
        # button_layout.addWidget(self.loading_bar)

        self.bottom_bar = QtWidgets.QHBoxLayout()
        self.bottom_bar.addWidget(self.icon_view)
        self.bottom_bar.addWidget(self.filter)
        self.bottom_bar.addWidget(self.loading_bar)

        button_layout.setAlignment(self.loading_bar, QtCore.Qt.AlignBottom)  # type: ignore

        for i in range(button_layout.count()):
            widget = button_layout.itemAt(i).widget()
            if widget:
                widget.setFixedHeight(40)
                widget.setFont(self.button_font)  # type: ignore
                widget.setStyleSheet(self.button_styleSheet)

        self.side_bar_layout = button_layout
        self.side_bar_scroll = QtWidgets.QScrollArea()
        self.side_bar_scroll.setLayout(self.side_bar_layout)
        self.side_bar_scroll.setWidgetResizable(True)

        self.stackedLayout.addWidget(self.thumbnail_layout)
        self.stackedLayout.addWidget(self.list_layout)

        self.body_layout.addLayout(self.stackedLayout)

        if show_side_bar:
            self.body_layout.addWidget(self.side_bar_scroll)

        self.main_layout.addLayout(self.title_layout)
        self.main_layout.addLayout(self.body_layout)
        self.main_layout.addLayout(self.bottom_bar)

        self.setLayout(self.main_layout)
        if not size:
            size = (1000, 800)

        self.resize(size[0], size[1])

        if position:
            self.move(position[0], position[1])

        self.body_layout.setStretch(0, 1)
        self.body_layout.setStretch(1, 0)
        self.setStyleSheet("background-color: #2d2d2d; color: #ffffff;")

        # Watermark
        self.watermark_label = QtWidgets.QLabel('www.huntervfx.com | 2023')
        self.watermark_label.setFont(self.watermark_font)
        self.watermark_label.setStyleSheet("color: rgb(200, 200, 200)")
        self.watermark_label.setAlignment(QtCore.Qt.AlignBottom | QtCore.Qt.AlignRight)
        self.main_layout.addWidget(self.watermark_label)

        # Combo box values
        self.directory_type.addItems(output_utils.Constants.DIRECTORY_TYPES.keys())  # type: ignore
        self.show_selection.addItems(output_utils.Constants.SHOWS)  # type: ignore

        # defaults
        self.show_selection.setCurrentText(start_project)
        log.debug("Setting show to: {}".format(start_project))
        self.directory_type.setCurrentText(start_type)
        self.sequence_toggle.setChecked(True)
        self.icon_view.setChecked(True)
        self.update_outputs()

        # Connections
        self.icon_view.toggled.connect(self.change_view)
        self.show_selection.currentTextChanged.connect(self.update_shots)
        self.show_selection.currentIndexChanged.connect(lambda: self.update_combo("show"))
        self.shot_selection.currentIndexChanged.connect(lambda: self.update_combo("shot"))
        self.directory_type.currentIndexChanged.connect(lambda: self.update_combo("type"))
        self.sequence_toggle.toggled.connect(self.update_outputs)
        self.filter.returnPressed.connect(self.update_outputs)
        self.size_slider.valueChanged.connect(self.update_outputs)

    def update_shots(self) -> bool:
        """
        Update the shots in the shot selection combobox, primarily used when changing shows.
        :return: True if successful
        """
        self.shot_selection.clear()
        self.shot_selection.addItems(output_utils.shots_from_show(self.show_selection.currentText()))
        return True

    def change_view(self):
        """
        Change the view of the files when the icon view checkbox is toggled.
        :return: Bool
        """
        if self.icon_view.isChecked():
            self.stackedLayout.setCurrentIndex(0)
        else:
            self.stackedLayout.setCurrentIndex(1)
        return True

    def update_combo(self, combo_type: Union[str, None] = None) -> bool:
        """
        Update the combo box based on the type
        :param combo_type: string combo box type
        :return: True if successful
        """
        current_project = self.show_selection.currentText()

        if combo_type == "show":
            self.shot_selection.clear()
            self.shot_selection.addItems(output_utils.shots_from_show(current_project, database=self.database))
        elif combo_type == "shot" or combo_type is "type":
            self.update_outputs()
            return True
        return True

    def update_outputs(self) -> bool:
        """
        Update the outputs based on the current combo box / filter values.
        :return: True if successful
        """
        try:
            self.loader_thread.stop()
            self.loader_thread.wait()
        except AttributeError:
            pass

        self.clear_flow_layout()
        self.clear_list_layout()

        output_reviewables = output_utils.get_reviewables(self.current_shots(),
                                                          self.directory_type.currentText(),
                                                          self.filter.text())
        log.debug("Updating outputs: {}".format(output_reviewables))
        self.update_flow_layout(output_reviewables)
        self.update_list_layout(output_reviewables)

        if not output_reviewables:
            return False

        self.loader_thread = ThumbnailLoader(output_reviewables)
        self.loader_thread.thumbnail_loaded.connect(self.update_thumbnail_image)
        self.loader_thread.start()
        return True

    def current_show(self) -> project.Project:
        """
        Get the current show from the combo box and return the project object.
        :return: String show name
        """
        project_instance = self.database.get_project(self.show_selection.currentText())
        return project_instance

    def current_shots(self) -> Optional[List[shot.Shot]]:
        """
        Get the current shot from the combo box and return the shot object.
        :return: List of shot objects
        """

        project_instance = self.database.get_project(self.show_selection.currentText())
        if not project_instance:
            return None
        do_sequence = self.sequence_toggle.isChecked()
        if not do_sequence:
            shot_instances = [project_instance.get_shot(self.shot_selection.currentText())]
        else:
            shot_instances = project_instance.get_shots()
        return shot_instances

    def clear_flow_layout(self) -> bool:
        """
        Clear all widgets from the flow layout.
        :return: True if successful
        """
        for i in reversed(range(self.flow_layout.count())):
            self.flow_layout.itemAt(i).widget().setParent(None)
        return True

    def clear_list_layout(self) -> bool:
        """
        Clear all widgets from the list layout.
        :return: True if successful
        """
        self.list_layout.clear()
        return True

    def update_flow_layout(self, output_reviewables: Optional[List[reviewable.Reviewable]]) -> bool:
        """
        Update the flow layout with the reviewables.
        :param output_reviewables: List of output reviewables
        :return: True if successful
        """
        buttons = []

        if not output_reviewables:
            return False

        for reviewable in output_reviewables:
            file_name = reviewable.asset_name
            button = QtWidgets.QToolButton()
            button.setText(file_name)
            pixmap = QtGui.QPixmap(output_utils.Constants.TEMP_IMAGE.system_path())
            button.setIcon(QtGui.QIcon(pixmap))
            size = self.size_slider.value()
            button.setIconSize(QtCore.QSize(size / 1.2, size))  # type: ignore
            button.setToolButtonStyle(QtCore.Qt.ToolButtonTextUnderIcon)  # type: ignore
            font = button.font()
            font.setPointSize(int(size / 25))
            button.setFont(font)
            button.setFixedSize(size, size)
            buttons.append(button)
            if not self.isDialog:
                button.clicked.connect(self.exit)

        for button in buttons:
            self.flow_layout.addWidget(button)
        return True

    def update_list_layout(self, output_reviewables: Optional[List[reviewable.Reviewable]]) -> bool:
        """
        Update the list layout with the reviewables.
        :param output_reviewables: List of output reviewables
        :return: True if successful
        """
        if not output_reviewables:
            return False
        self.list_layout.setRowCount(len(output_reviewables))
        for count, reviewable in enumerate(output_reviewables):
            file_name = reviewable.asset_name
            self.list_layout.setItem(count, 0, QtWidgets.QTableWidgetItem(file_name))
        return True

    def update_thumbnail_image(self, thumbnail: 'QtGui.QPixmap', iter_num: int) -> bool:
        """
        Update the button thumbnail
        :param thumbnail: QPixmap thumbnail image to set
        :param iter_num: int iteration number / index of the button to update
        :return: True if successful
        """
        try:
            log.debug("Updating button thumbnail: {0}".format(iter_num))
            button = self.flow_layout.itemAt(iter_num).widget()
            button.setIcon(QtGui.QIcon(thumbnail))
            if self.loading_bar.value() < 95:
                # change color to yellow
                self.loading_bar.setStyleSheet("QProgressBar::chunk {background-color: #FFD700;}")
            else:
                # change color to green
                self.loading_bar.setStyleSheet("QProgressBar::chunk {background-color: #00FF00;}")
            return True
        except AttributeError:
            pass

    def exit(self) -> str:
        """
        Close the window and stop the thread. Return the current item filepath.
        """
        selected_item = self.sender()
        self.loader_thread.stop()
        log.debug(f"Selected item: {selected_item.text}")
        if selected_item:
            log.debug(selected_item.text())
            self.return_value['filepath'] = selected_item.text()
            self.accept()