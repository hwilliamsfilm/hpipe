"""
Pipe Manager GUI for viewing outputs, comps, and renders.
"""

import sys
if sys.version_info <= (3, 8):
    from PySide2 import QtWidgets, QtCore, QtGui  # type: ignore
    from typing_extensions import TypedDict, Literal, overload
else:
    from PySide6 import QtWidgets, QtCore, QtGui

from core import data_manager, project, shot
from apps.pipeDisplay import output_widgets, output_utils
from core.hutils import logger
from typing import *
from assets import reviewable
import time

log = logger.setup_logger()
log.debug("manager_gui.py loaded")


class StageLoader(QtCore.QThread):
    """
    Thread for loading thumbnails in the background based on the directories in the project.
    """
    stage_loaded = QtCore.Signal(QtGui.QPixmap, int)

    def __init__(self, shot_list):
        super().__init__()
        self.shot_list = shot_list

        # need to keep track of the thread's running state so we can prevent the thread from emitting signals after
        # it's already been stopped
        self._running = True

    def run(self):
        """
        Load thumbnails for each reviewable in the project. Emit a signal when each thumbnail is loaded with the
        index of the reviewable in the list.
        """
        log.warning("Loading stage")
        # for index, reviewable_instance in enumerate(self.reviewable_list):
        #     image = reviewable_instance.get_thumbnail_image()
        #     if image:
        #         thumbnail = QtGui.QPixmap(image.system_path())
        #     else:
        #         thumbnail = QtGui.QPixmap(output_utils.Constants.TEMP_IMAGE.system_path())
        #     if self._running:
        #         self.thumbnail_loaded.emit(thumbnail, index)
        #     time.sleep(0.001)

    def stop(self):
        self._running = False
        self.requestInterruption()
        self.wait()


class SequenceUSDViewer(QtWidgets.QWidget):
    """
    Project Overview Panel where I can see and edit all projects and shots. This is a project management tool
    and not a viewer.
    """
    def __init__(self, parent=None, font_scale: float = 1.0, start_project: str = output_utils.Constants.START_PROJECT):
        super(SequenceUSDViewer, self).__init__(parent)

        self.example_shot_dictionary = {
            'shot_title': "shot_001",
            'variants': {
                'trak': 'A01',
                'comp': 'A03',
                'chrGodzilla': 'A01_01',
                'chrKong': 'A02',
            }
        }

        small_font = int(15 * font_scale)
        large_font = int(40 * font_scale)
        medium_font = int(25 * font_scale)

        self.button_font = QtGui.QFont("Arial", small_font)
        self.button_styleSheet = "background-color: #2d2d2d; color: #ffffff;"
        self.title_font = QtGui.QFont("Helvetica", large_font, QtGui.QFont.Bold)  # type: ignore
        self.title_font.setItalic(True)
        self.shot_font = QtGui.QFont("Helvetica", small_font, QtGui.QFont.Bold)  # type: ignore
        self.shot_font.setItalic(True)
        self.subtitle_font = QtGui.QFont("Helvetica", small_font, QtGui.QFont.Light)  # type: ignore
        self.subtitle_font.setItalic(True)
        self.watermark_font = QtGui.QFont("Helvetica", medium_font, QtGui.QFont.Light)  # type: ignore

        self.setWindowTitle('Sequence USD Viewer')

        self.shot_list = {}

        temp_stage_list: List[Dict] = []
        for i in range(5):
            self.example_shot_dictionary["name"] = f"Shot {i}"
            temp_stage_list.append(self.example_shot_dictionary.copy())

        self.temp_stage_list = temp_stage_list

        self.title_layout = QtWidgets.QHBoxLayout()
        self.title_label = QtWidgets.QLabel('Sequence USD Viewer')
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

        self.list_layout = QtWidgets.QTableWidget()
        self.list_layout.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)  # type: ignore
        self.list_layout.verticalHeader().setVisible(False)
        self.list_layout.setColumnCount(1)
        self.list_layout.setAlternatingRowColors(True)
        self.list_layout.horizontalHeader().setVisible(False)
        self.list_layout.setStyleSheet(
            "alternate-background-color: #2d2d2d; background-color: #1d1d1d; color: #ffffff;")
        self.list_layout.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)  # type: ignore

        self.show_selection = QtWidgets.QComboBox()
        self.sequence_selection = QtWidgets.QComboBox()

        self.filter = QtWidgets.QLineEdit()
        self.filter.setPlaceholderText("Asset Filter")
        self.version_filter = QtWidgets.QLineEdit()
        self.version_filter.setPlaceholderText("Version Filter")
        self.icon_view = QtWidgets.QCheckBox("Table View")

        self.size_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)  # type: ignore
        self.size_slider.setMinimum(50)
        self.size_slider.setMaximum(400)
        self.size_slider.setValue(200)
        self.size_slider.setTickInterval(10)
        self.size_slider.setTickPosition(QtWidgets.QSlider.TicksBelow)  # type: ignore

        button_layout = QtWidgets.QVBoxLayout()
        button_layout.setAlignment(QtCore.Qt.AlignTop)  # type: ignore
        button_layout.addWidget(self.filter)
        button_layout.addWidget(self.version_filter)
        # button_layout.addWidget(output_widgets.QHLine())  # type: ignore
        button_layout.addWidget(output_widgets.QHLine())  # type: ignore
        button_layout.addWidget(self.show_selection)
        button_layout.addWidget(self.sequence_selection)
        button_layout.addWidget(output_widgets.QHLine())  # type: ignore
        # button_layout.addWidget(self.size_slider)

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
        self.body_layout.addWidget(self.side_bar_scroll)
        self.main_layout.addLayout(self.title_layout)
        self.main_layout.addLayout(self.body_layout)
        self.setLayout(self.main_layout)
        self.resize(1000, 800)
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
        self.show_selection.addItems(output_utils.Constants.SHOWS)  # type: ignore

        # Connections
        self.icon_view.stateChanged.connect(self.change_view)
        # update output if filter enter is pressed
        self.filter.returnPressed.connect(self.update_outputs)
        self.version_filter.returnPressed.connect(self.update_outputs)

        # init
        self.update_outputs(reload_stage=True)

    def update_outputs(self, reload_stage=False) -> bool:
        """
        Update the outputs based on the current combo box / filter values.
        :return: True if successful
        """
        self.clear_flow_layout()
        if reload_stage:
            # change shot list here initially
            pass
        self.update_flow_layout()
        if reload_stage:
            self.refresh_stage_variants() # kick off the thread to reload the stage variants

    def refresh_stage_variants(self) -> bool:
        """
        Update the stage variants based on the current combo box / filter values. This should happen whenever
        the show/seq is changed.
        """
        # self.
        self.loader_thread = StageLoader(self.shot_list)
        self.loader_thread.stage_loaded.connect(self.update_stage_variants)
        self.loader_thread.start()
        return True

    def change_view(self, state):
        """
        Change the view between report card and table view
        """
        if state:
            self.stackedLayout.setCurrentIndex(1)
        else:
            self.stackedLayout.setCurrentIndex(0)

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

    def update_flow_layout(self) -> bool:
        """
        Update the flow layout with the reviewables.
        :param output_reviewables: List of output reviewables
        :return: True if successful
        """
        output_reviewables = self.temp_stage_list
        filter = self.filter.text()
        version_filter = self.version_filter.text()

        cards = []
        skip = False

        if not output_reviewables:
            return False

        for reviewable in output_reviewables:
            layout = QtWidgets.QVBoxLayout()
            layout.setContentsMargins(5, 5, 5, 5)
            layout.setSpacing(5)
            layout.setAlignment(QtCore.Qt.AlignTop)  # type: ignore
            shot_title = reviewable["name"]
            label = QtWidgets.QLabel(shot_title)
            label.setFont(self.shot_font)
            tree_widget = QtWidgets.QTreeWidget()
            tree_widget.setHeaderHidden(True)
            tree_widget.setAlternatingRowColors(True)
            tree_widget.setColumnCount(2)

            for k,v in reviewable["variants"].items():
                if filter not in k:
                    continue
                if version_filter not in v:
                    continue
                variant_name = k
                variant_name_item = QtWidgets.QTreeWidgetItem(tree_widget, [variant_name])
                variant_version = v
                QtWidgets.QTreeWidgetItem(variant_name_item, [variant_version])

            tree_widget.expandAll()

            if not tree_widget.topLevelItemCount():
                skip = True

            layout.addWidget(label)
            layout.addWidget(tree_widget)
            widget = QtWidgets.QWidget()
            widget.setLayout(layout)
            widget.setStyleSheet("alternate-background-color: #1d1d1d; background-color: #2d2d2d; color: #ffffff;")


            if skip:
                continue

            cards.append(widget)

        for card in cards:
            self.flow_layout.addWidget(card)
        return True

    def update_stage_variants(self, stage_variants):
        """
        Update the stage variants
        :param stage_variants: List of stage variants
        :return: True if successful
        """
        log.debug(f"Updating stage variants: {stage_variants}")
        return