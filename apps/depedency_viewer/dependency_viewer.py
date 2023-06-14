"""
UI for viewing pipe dependencies
"""

from core.hutils import path
from core.hutils import osutil
from core import db

from PySide2.QtCore import QPoint, QRect, QSize, Signal, QThread, Qt
from PySide2.QtGui import QIcon, QPixmap, QCursor, QBrush, QColor, QFont

from PySide2.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLineEdit,
    QLayout,
    QMenu,
    QScrollArea,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QStackedLayout,
    QTableWidget,
    QToolButton,
    QSizePolicy,
    QSlider,
    QProgressBar,
)

import time
import os
import sys
import re

from concurrent.futures import ThreadPoolExecutor


def _shots_for_show(show):
    """
    Gets the shots for a given show.
    :param str show: the show name to get the shots for, case-sensitive
    :return list: List of string shot names.
    """
    shots = db.Db().get_project(show).get_shots()
    return [shot.name for shot in shots]


def _outputs_in_directory(directory):
    """
    Return the "outputs" for a given directory. Some subjectivity and filtering is applied to determine what is an
    output.
    :param str directory: The directory to search for outputs.
    :return list: List of output paths as strings.
    """
    outputs = []

    # check if the directory exists and is a directory
    if not path.verify_directory(directory):
        return []
    
    # loop over directories and files in the directory
    for item in os.listdir(directory):

        # if starts with a period, skip it
        if item.startswith('.'):
            continue

        # if the item is a directory, add it to the list
        if os.path.isdir(os.path.join(directory, item)):
            # append full path
            outputs.append(os.path.join(directory, item))

    return outputs


def _sort_files(files):
    """
    Sorts a list of files by version in ascending order, while keeping similar prefixed files together.
    :param list files:
    :return:
    """
    def version_key(filename):
        """Return the version number of a filename, or an empty tuple if there is no version."""
        match = re.search(r'([A-Z])(\d+)', filename)
        if match:
            letter, number = match.groups()
            return (int(number),)
        else:
            return ()

    def prefix_key(filename):
        """Return the prefix of a filename."""
        match = re.search(r'(.+)_([A-Z]\d+)\.txt', filename)
        if match:
            return match.group(1)
        else:
            return filename

    filenames = files

    # Group the filenames by prefix
    groups = {}
    for filename in filenames:
        prefix = prefix_key(filename)
        if prefix in groups:
            groups[prefix].append(filename)
        else:
            groups[prefix] = [filename]

    # Sort the groups by prefix
    sorted_groups = sorted(groups.items())

    # Sort the filenames within each group by version
    grouped_filenames = []
    for prefix, filenames in sorted_groups:
        sorted_filenames = sorted(filenames, key=version_key)
        grouped_filenames.append(sorted_filenames)

    # flatten list
    grouped_filenames = [item for sublist in grouped_filenames for item in sublist]
    return grouped_filenames

def _log(message, severity):
    """
    Log a message to the console
    :param message: String
    :param severity: String
    :return: None
    """
    return
    from utility import logger
    logger.log(message, severity)
    return True

def _open_file(file):
    """
    Open a file in the default application
    :param file: String
    :return: None
    """
    osutil.open_file(file)

def _get_version_from_directory(directory):
    """
    Extracts the version from a filename if it exists in the format 'A12', 'B07', 'B87', 'C05', etc.
    Returns the version as a string, or None if no version is found.
    """
    import re
    pattern = r"([^\\/]+)([A-Z]\d{2})"  # Regex pattern for the version format
    _log("pattern: {}".format(directory), "WARNING")
    match = re.search(pattern, directory)
    if match:
        return match.groups()
    return (os.path.basename(directory), 'A01')

def _sort_filenames_by_version(filenames, latest_only=False):
    """
    Sorts a list of filenames by version in ascending order, while keeping similar prefixed filenames together.
    """
    _log("filenames: {}".format(filenames), "WARNING")
    # Group the filenames by prefix
    prefix_groups = {}
    for filename in filenames:
        prefix = _get_version_from_directory(filename)[0]
        if prefix not in prefix_groups:
            prefix_groups[prefix] = []
        prefix_groups[prefix].append(filename)

    _log("prefix_groups: {}".format(prefix_groups), "WARNING")
    # Sort each group by version number
    sorted_filenames = []
    for prefix in sorted(prefix_groups.keys()):
        filenames = prefix_groups[prefix]
        sorted_filenames += sorted(filenames, key=lambda x: _get_version_from_directory(x))

    latest_filenames = []
    for prefix, filenames in prefix_groups.items():
        versions = [_get_version_from_directory(filename) for filename in filenames]
        if not versions:
            latest_filenames.append(filenames[-1])
            continue
        sorted_indices = sorted(range(len(versions)), key=lambda i: versions[i][1])
        sorted_prefixes = [filenames[i] for i in sorted_indices]
        latest_filenames.append(sorted_prefixes[-1])

    if latest_only:
        _log("Latest filenames: {}".format(latest_filenames), "ERROR")
        return latest_filenames
    else:
        _log("sorted_filenames: {}".format(sorted_filenames), "ERROR")
        return sorted_filenames

class Constants():
    """
    Constants for the Dependency Viewer
    """
    TEMP_IMAGE = path.convertPath(r'Y:\_houdini_\icons\main.png')
    WINDOW_TITLE = "Dependency Viewer"
    #STARTING_DIRECTORY = [path.convertPath(r'Y:\projects\2023\wound_wood\shots\WW_025_0005\output\comp')]
    STARTING_DIRECTORY = []

    # TODO: add more directory types
    # adds directory names for the dropdown and the relative path to the directory from the shot directory
    DIRECTORY_TYPES = {
        "Comp": path.convertPath(r"Y:\projects\2023\{show}\shots\{shot}\output\comp"),
        "Plate": path.convertPath(r"Y:\projects\2023\{show}\shots\{shot}\plate"),
        "Workarea": path.convertPath(r"Y:\projects\2023\{show}\shots\{shot}\output\_workarea"),
        "Renders": path.convertPath(r"Y:\projects\2023\{show}\shots\{shot}\output\render"),
        "Ref": path.convertPath(r"Y:\projects\2023\{show}\shots\{shot}\ref")
    }

    TEMP_ICON = path.convertPath(r'Y:\_houdini_\icons\main.png')

    THUMBNAIL_BATCH_SIZE = 50

    from core import db
    SHOWS = [p.name for p in db.Db().get_projects()]

    DEFAULT_PROJECT = "wound_wood"
    DEFAULT_TYPE = "Plate"
    DEFAULT_FILTER = "ref"
    DEFAULT_SEQUENCE_TOGGLE = True


class ThumbnailLoader(QThread):
    thumbnail_loaded = Signal(QPixmap, int)

    def __init__(self, batch):
        super().__init__()
        self.directories = batch
        self._running = True

    def run(self):
        for i, directory in enumerate(self.directories):
            if not self._running:
                break
            for file in os.listdir(directory):
                if not self._running:
                    break
                if file.endswith('.png') or file.endswith('.jpg'):
                    filepath = os.path.join(directory, file)
                    thumbnail = QPixmap(filepath)
                    break
                else:
                    thumbnail = QPixmap(Constants.TEMP_IMAGE)

            if self._running:
                self.thumbnail_loaded.emit(thumbnail, i)

            # sleep for .01 seconds to allow the UI to update
            time.sleep(0.01)

    def stop(self):
        self._running = False
        self.requestInterruption()
        self.wait()



class QHLine(QFrame):
    def __init__(self):
        super(QHLine, self).__init__()
        self.setFrameShape(QFrame.HLine)
        self.setFrameShadow(QFrame.Sunken)


class FlowLayout(QLayout):
    """
    A flow layout that automatically wraps to the next line if there is no space
    on the current line.
    """
    def __init__(self, parent=None, margin=0, spacing=-1):
        super(FlowLayout, self).__init__(parent)
        if parent is not None:
            self.setContentsMargins(margin, margin, margin, margin)
        self.setSpacing(spacing)
        self.itemList = []

    def __del__(self):
        item = self.takeAt(0)
        while item:
            item = self.takeAt(0)

    def addItem(self, item):
        """Add an item to the layout."""
        self.itemList.append(item)

    def count(self):
        """Return the number of items in the layout."""
        return len(self.itemList)

    def itemAt(self, index):
        """Return the item at the given index."""
        if index >= 0 and index < len(self.itemList):
            return self.itemList[index]
        return None

    def takeAt(self, index):
        """Remove and return the item at the given index."""
        if index >= 0 and index < len(self.itemList):
            return self.itemList.pop(index)

        return None

    def expandingDirections(self):
        """Return the expanding directions."""
        return Qt.Orientations(Qt.Orientation(0))

    def hasHeightForWidth(self):
        """Return True if the layout has a height for width."""
        return True

    def heightForWidth(self, width):
        """Return the height for the given width."""
        height = self.doLayout(QRect(0, 0, width, 0), True)
        return height

    def setGeometry(self, rect):
        """Set the geometry of the layout."""
        super(FlowLayout, self).setGeometry(rect)
        self.doLayout(rect, False)

    def sizeHint(self):
        """Return the size hint."""
        return self.minimumSize()

    def minimumSize(self):
        """Return the minimum size."""
        size = QSize()

        for item in self.itemList:
            size = size.expandedTo(item.minimumSize())

        margin, _, _, _ = self.getContentsMargins()

        size += QSize(2 * margin, 2 * margin)

        # set minimum horizontal size to 100
        size.setWidth(max(size.width(), 50))


        return size


    def doLayout(self, rect, testOnly):
        """Perform the layout."""
        x = rect.x()
        y = rect.y()
        lineHeight = 0
        for item in self.itemList:
            wid = item.widget()
            spaceX = self.spacing() + wid.style().layoutSpacing(QSizePolicy.PushButton, QSizePolicy.PushButton,
                                                                Qt.Horizontal)
            spaceY = self.spacing() + wid.style().layoutSpacing(QSizePolicy.PushButton, QSizePolicy.PushButton,
                                                                Qt.Vertical)


            nextX = x + item.sizeHint().width() + spaceX
            if nextX - spaceX > rect.right() and lineHeight > 0:
                x = rect.x()
                y = y + lineHeight + spaceY
                nextX = x + item.sizeHint().width() + spaceX
                lineHeight = 0

            if not testOnly:
                item.setGeometry(QRect(QPoint(x, y), item.sizeHint()))
            x = nextX
            lineHeight = max(lineHeight, item.sizeHint().height())

        return y + lineHeight - rect.y()

    def indexAt(self, pos):
        """Return the index of the widget at the given position."""
        for i, item in enumerate(self.itemList):
            if item.geometry().contains(pos):
                return i
        return -1


class DependencyViewer(QWidget):
    def __init__(self):
        super().__init__()

        # set initial window vars
        self.setWindowTitle(Constants.WINDOW_TITLE)
        self.directories = Constants.STARTING_DIRECTORY

        self.thumbnail_loader_pool = ThreadPoolExecutor(max_workers=4)

        # BUILD UI
        layout = QHBoxLayout()
        self.stackedLayout = QStackedLayout()

    ##### PAGE 1 #####
        self.flow_layout = FlowLayout()
        self.thumbnail_layout = self.create_thumbnail_layout()

        # add context menu to thumbnail layout
        self.thumbnail_layout.setContextMenuPolicy(Qt.CustomContextMenu)
        self.thumbnail_layout.customContextMenuRequested.connect(self.show_context_menu)

        # add actions to context menu
        self.context_menu = QMenu(self)
        self.open_action = self.context_menu.addAction("Open In Explorer")
        self.open_action.triggered.connect(self.open_in_explorer)

        # add open in rv action to context menu
        self.open_in_rv_action = self.context_menu.addAction("Open In RV")
        self.open_in_rv_action.triggered.connect(self.open_in_rv)

        # add move to delivery action to context menu
        self.move_to_delivery_action = self.context_menu.addAction("Move To Delivery")
        self.move_to_delivery_action.triggered.connect(self.move_to_delivery)


    ##### PAGE 2 #####
        self.list_layout = self.create_list_layout()

        # add context menu to list layout
        self.list_layout.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list_layout.customContextMenuRequested.connect(self.show_context_menu)


    #### SIDE BAR ####
        # add combo box to select show
        self.show_selection = QComboBox()
        self.seq_selection = QComboBox()
        self.shot_selection = QComboBox()
        self.directory_type = QComboBox()

        self.directory_type.addItems(Constants.DIRECTORY_TYPES.keys())
        self.show_selection.addItems(Constants.SHOWS)

        # add sequence toggle checkbox
        self.show_toggle = QCheckBox("Browse by Show")
        self.show_toggle.setChecked(True)

        self.filter = QLineEdit()
        self.filter.setPlaceholderText("Filter")

        # find shot button
        self.find_shot = QLineEdit()
        self.find_shot.setPlaceholderText("Find Shot")
        # on enter pressed event
        self.find_shot.returnPressed.connect(self.find_shot_pressed)

        # icon view toggle
        self.icon_view = QCheckBox("Icon View")
        self.icon_view.setChecked(True)

        # add latest version toggle
        self.latest_version = QCheckBox("Latest Version Only")
        self.latest_version.setChecked(False)

        # add size slider
        self.size_slider = QSlider(Qt.Horizontal)
        self.size_slider.setMinimum(50)
        self.size_slider.setMaximum(400)
        self.size_slider.setValue(200)
        self.size_slider.setTickInterval(10)
        self.size_slider.setTickPosition(QSlider.TicksBelow)

        # create loading bar
        self.loading_bar = QProgressBar()
        self.loading_bar.setRange(0, 100)
        self.loading_bar.setTextVisible(False)

        # make complete
        self.loading_bar.setValue(100)

        # create main layout
        self.side_bar_layout = self.create_side_bar()
        # make side_bar_layout scrollable
        self.side_bar_scroll = QScrollArea()
        self.side_bar_scroll.setLayout(self.side_bar_layout)
        # scroll if needed
        self.side_bar_scroll.setWidgetResizable(True)


        # dynamically change seq combo box based on show
        self.show_selection.currentIndexChanged.connect(lambda: self.update_combo(self.show_selection, "show"))
        self.shot_selection.currentIndexChanged.connect(lambda: self.update_combo(self.shot_selection, "shot"))
        self.directory_type.currentIndexChanged.connect(lambda: self.update_combo(self.directory_type, "type"))
        self.icon_view.stateChanged.connect(self.change_view)
        self.size_slider.valueChanged.connect(self.update_button_size)
        self.latest_version.stateChanged.connect(self.refresh_directories)
        self.filter.returnPressed.connect(self.filter_changed)

        self.show_toggle.stateChanged.connect(self.refresh_directories)
        self.filter.returnPressed.connect(self.refresh_files)

    # ADD LAYOUTS TO STACKED LAYOUT
        self.stackedLayout.addWidget(self.thumbnail_layout)
        self.stackedLayout.addWidget(self.list_layout)

    # ADD LAYOUTS TO MAIN LAYOUT
        layout.addLayout(self.stackedLayout)

        #layout.addLayout(self.side_bar_layout)

        # add scroll area to main layout
        layout.addWidget(self.side_bar_scroll)

    # SET MAIN LAYOUT
        self.setLayout(layout)

        # set size
        self.resize(1000, 800)
        #self.side_bar_layout.setSizeConstraint(QLayout.SetFixedSize)
        layout.setStretch(0, 1)
        layout.setStretch(1, 0)

        # make dark theme
        self.setStyleSheet("background-color: #2d2d2d; color: #ffffff;")

        # # set defaults
        self.show_selection.setCurrentText(Constants.DEFAULT_PROJECT)
        self.directory_type.setCurrentText(Constants.DEFAULT_TYPE)
        self.filter.setText(Constants.DEFAULT_FILTER)
        self.show_toggle.setChecked(Constants.DEFAULT_SEQUENCE_TOGGLE)
        self.filter_changed()
        self.update_combo(self.show_selection, "show")
        # self.sequence_toggle.setChecked(Constants.DEFAULT_SEQUENCE_TOGGLE)

    # LAYOUT FUNCTIONS
    def create_thumbnail_layout(self):
        """
        Create the thumbnail layout
        """
        # create the scroll area and flowlayout
        scroll_area = QScrollArea()
        flowlayout = self.flow_layout

        # use a widget to contain the flow layout
        container = QWidget()
        container.setLayout(flowlayout)

        # add the widget to the scroll area
        scroll_area.setWidget(container)
        scroll_area.setWidgetResizable(True)
        scroll_area.setMinimumWidth(20)
        scroll_area.setMaximumWidth(5000)

        return scroll_area

    @staticmethod
    def create_list_layout():
        table = QTableWidget()
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        # vertical header is hidden
        table.verticalHeader().setVisible(False)
        # set number of columns
        table.setColumnCount(2)
        return table

    def create_side_bar(self):
        """
        Create the sidebar
        :return: QVBoxLayout
        """
        button_layout = QVBoxLayout()
        button_layout.setAlignment(Qt.AlignTop)

        # add icon view toggle
        button_layout.addWidget(self.icon_view)
        # add combo boxes to layout
        button_layout.addWidget(self.find_shot)
        # add horizontal line
        button_layout.addWidget(QHLine())
        button_layout.addWidget(self.directory_type)
        button_layout.addWidget(QHLine())
        button_layout.addWidget(self.show_selection)
        # button_layout.addWidget(self.seq_selection)
        button_layout.addWidget(self.shot_selection)
        button_layout.addWidget(QHLine())
        button_layout.addWidget(self.show_toggle)
        button_layout.addWidget(QHLine())
        button_layout.addWidget(self.filter)
        button_layout.addWidget(QHLine())
        button_layout.addWidget(self.latest_version)
        button_layout.addWidget(QHLine())
        button_layout.addWidget(self.size_slider)
        button_layout.addWidget(self.loading_bar)

        # # add space between combo boxes
        # button_layout.addSpacing(20)

        # set default for show selection combo box
        self.show_selection.setCurrentText(Constants.DEFAULT_PROJECT)

        # move the loading bar to the bottom
        button_layout.setAlignment(self.loading_bar, Qt.AlignBottom)

        # make all widgets larger
        for i in range(button_layout.count()):
            widget = button_layout.itemAt(i).widget()
            if widget:
                widget.setFixedHeight(40)
                widget.setFont(QFont("Arial", 10))
                widget.setStyleSheet("background-color: #2d2d2d; color: #ffffff;")

        # set combo box height
        self.show_selection.setFixedHeight(40)
        self.shot_selection.setFixedHeight(40)
        self.directory_type.setFixedHeight(40)
        self.filter.setFixedHeight(40)
        self.find_shot.setFixedHeight(40)

        return button_layout

    # UI UPDATE FUNCTIONS
    def change_view(self):
        """
        Change the view of the files
        :return: Bool
        """
        if self.icon_view.isChecked():
            self.stackedLayout.setCurrentIndex(0)
        else:
            self.stackedLayout.setCurrentIndex(1)
        return True

    def update_combo(self, combo, combo_type=None):
        """
        Update the combo box based on the type
        :param combo: QComboBox
        :param combo_type: String
        :return: Bool
        """

        current_show = self.show_selection.currentText()

        if combo_type == "show":
            # update the sequence combo box
            shots = _shots_for_show(current_show)
            self.shot_selection.clear()
            self.shot_selection.addItems(shots)

        elif combo_type == "shot":
            # update the directory type
            self.refresh_directories()

        elif combo_type == "type":
            # update the directory type
            self.refresh_directories()

        return True

    def refresh_directories(self):
        """
        Refresh the directories
        """
        show = self.show_selection.currentText()
        shot = self.shot_selection.currentText()
        type = self.directory_type.currentText()

        directory_pattern = Constants.DIRECTORY_TYPES[type]

        directories = []
        if self.show_toggle.isChecked():
            for shot in _shots_for_show(show):
                directory = directory_pattern.format(show=show, shot=shot)
                directories.append(directory)
        else:
            directory = directory_pattern.format(show=show, shot=shot)
            directories.append(directory)

        #FIXME: Should this be a signal or set in the __init__? Might need to pass the directories into the
        #       refresh_files function, but could be troublesome if refresh files is called from multiple places
        #       which is the plan at the moment

        # stop secondary threads
        try:
            self.loader_thread.stop()
        except AttributeError:
            pass

        self.directories = directories
        self.refresh_files()

        _log("Directories: {}".format(directories), "WARNING")

        return directories

    def refresh_files(self):
        """
        Refresh the files
        """

        # loop through directories and find version directories
        version_directories = []
        for directory in self.directories:
            version_directories.extend(_outputs_in_directory(directory))

        filter_text = self.filter.text()
        if filter_text != "":
            filtered_directories = []
            _log("Filtering by: {}".format(filter_text), "ERROR")
            for directory in version_directories:
                # get basename of directory
                basename = os.path.basename(directory)
                if filter_text in basename:
                    filtered_directories.append(directory)
            version_directories = filtered_directories

        _log("Version Directories: {}".format('\n'.join(version_directories)), "WARNING")

        latest_only = self.latest_version.isChecked()
        version_directories = _sort_filenames_by_version(version_directories, latest_only)

        self.update_table(version_directories)
        self.update_flow_layout(version_directories)

        return True

    def find_shot(self):
        return NotImplemented

    # UPDATE PAGES
    def update_table(self, version_directories):
        """
        Update the table
        """
        _log("Updating table", "WARNING")
        table = self.list_layout
        table.clear()
        table.setRowCount(len(version_directories))
        table.setColumnCount(2)
        table.setHorizontalHeaderLabels(["Version", "Filename"])

        _log("Version Directories: {}".format(version_directories), "WARNING")
        for i, directory in enumerate(version_directories):
            file_name = os.path.basename(directory)
            version = _get_version_from_directory(directory)[1]
            table.setItem(i, 1, QTableWidgetItem(file_name))

            table.setItem(i, 0, QTableWidgetItem(version))

            # set version column to be bold
            table.item(i, 0).setFont(QFont("Arial", 10, QFont.Bold))
            # set version column text to red
            table.item(i, 0).setForeground(QBrush(QColor(255, 0, 0)))

        # set column 1 to shrink to contents
        table.resizeColumnsToContents()
        table.setColumnWidth(1, 0)

        #resize header to contents
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)


        self.list_layout = table
        return True

    def update_flow_layout(self, version_directories):
        """
        Update the flow layout
        """
        _log("Updating flow layout", "WARNING")

        # stop secondary threads
        try:
            self.loader_thread.stop()
            self.loader_thread.wait()
        except AttributeError:
            pass

        # get flow layout inside scroll area
        flow_layout = self.flow_layout

        # clear the layout
        for i in reversed(range(flow_layout.count())):
            flow_layout.itemAt(i).widget().setParent(None)

        buttons = []

        for directory in version_directories:
            file_name = os.path.basename(directory)

            button = QToolButton()
            button.setText(file_name)

            # set icon to temp image
            pixmap = QPixmap(Constants.TEMP_IMAGE)
            button.setIcon(QIcon(pixmap))

            # align text to bottom
            # current icon size
            size = self.size_slider.value()
            button.setIconSize(QSize(size/1.2, size))
            button.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
            font = button.font()
            font.setPointSize(size/25)
            button.setFont(font)

            # set button to size of thumbnail
            button.setFixedSize(size, size)

            buttons.append(button)

        # add buttons to layout
        for button in buttons:
            flow_layout.addWidget(button)

        # FIXME: EXPERIMENTAL - working on threading the thumbnail loading
        self.version_directories = version_directories
        self.loader_thread = ThumbnailLoader(version_directories)
        self.loader_thread.thumbnail_loaded.connect(self.update_button_thumbnail)
        self.loader_thread.start()

    def update_button_thumbnail(self, thumbnails, iter_num):
        """
        Update the button thumbnail
        :param thumbnails:
        :param iter_num:
        :return:
        """
        # FIXME: try except because of the way the thread is being stopped, need to find a better way
        try:
            _log("SIGNAL CAUGHT: batch {0}, thumbnails {1}".format(iter_num, thumbnails), "DEBUG")
            button = self.flow_layout.itemAt(iter_num).widget()
            button.setIcon(QIcon(thumbnails))
            amt = len(self.version_directories)

            # FIXME: This probably shouldnt be here
            _log("Amount: {0}".format(amt), "DEBUG")
            self.loading_bar.setValue((iter_num*100)/amt)
            if self.loading_bar.value() < 95:
                # change color to yellow
                self.loading_bar.setStyleSheet("QProgressBar::chunk {background-color: #FFD700;}")
            else:
                # change color to green
                self.loading_bar.setStyleSheet("QProgressBar::chunk {background-color: #00FF00;}")
        except AttributeError:
            _log("Attribute Error: {0}".format(iter_num), "DEBUG")
            pass

    def update_button_size(self):
        """
        Update the button size
        """
        size = self.size_slider.value()
        for i in range(self.flow_layout.count()):
            button = self.flow_layout.itemAt(i).widget()
            button.setFixedSize(size, size)
            # set icon size
            button.setIconSize(QSize(size/1.2, size))
            # resize text
            font = button.font()
            font.setPointSize(size/25)
            button.setFont(font)

        return True

    def find_shot_pressed(self):
        """
        Find shot pressed
        """
        from core import db

        _log("Find shot pressed", "WARNING")
        tokens = self.find_shot.text().split(" ")
        if len(tokens) == 2:
            # has show and shot
            show = tokens[0]
            shot = tokens[1]
        elif len(tokens) == 1:
            # only has shot
            show = self.show_selection.currentText()
            shot = tokens[0]

        _log("Show: {0}, Shot: {1}".format(show, shot), "WARNING")

        database = db.Db()
        # check if show exists
        if not database.get_project(show):
            _log("Show does not exist", "ERROR")
            return False

        # check if shot exists
        if not database.get_project(show).get_shot(shot, database=database):
            _log("Shot does not exist", "ERROR")
            return False

        self.find_shot.clear()
        self.show_selection.setCurrentText(show)
        self.shot_selection.setCurrentText(shot)

        return True

    def filter_changed(self):
        """
        Filter changed
        """
        _log("Filter changed", "WARNING")
        self.refresh_directories()
        return

    # CONTEXT MENU FUNCTIONS
    def show_context_menu(self, pos):
        """
        Context menu
        """
        # shwo context menu
        menu = self.context_menu
        menu.exec_(self.mapToGlobal(pos))

    def open_in_explorer(self):
        """
        Open the selected file in explorer
        """
        _log("Opening in explorer", "WARNING")

        filepaths = self.getSelectedFilepaths()

        _log("Opening: {}".format(filepaths), "WARNING")
        if path.get_system() == "windows":
            for filepath in filepaths:
                os.startfile(filepath)


    def open_in_rv(self):
        """
        Open the selected file in rv
        """
        _log("Opening in rv", "WARNING")

        filepaths = self.getSelectedFilepaths()

        # get first image file in each filepath
        for i, filepath in enumerate(filepaths):
            files = os.listdir(filepath)
            for file in files:
                if file.endswith(".jpg") or file.endswith(".png") or file.endswith(".exr"):
                    filepaths[i] = os.path.join(filepath, file)
                    break

        _log("Opening: {}".format(filepaths), "WARNING")
        if path.get_system() == "windows":
            rv = r"C:\Program Files\ShotGrid\RV-2022.3.1\bin\rv.exe"
        elif path.get_system() == "linux":
            rv = "/home/hunter/rez/rv-centos7-x86-64-2022.3.1/bin/rv"
        elif path.get_system() == "osx":
            rv = "/Applications/RV-7.0.0.app/Contents/MacOS/rv"

        import subprocess
        cmd = [rv, "-layout", "packed", "-view", "defaultLayout"] + filepaths
        subprocess.Popen(cmd)

        # subprocess.Popen([rv] + filepaths)

    def move_to_delivery(self):
        return NotImplemented

    def getSelectedFilepaths(self):
        # chck if list or flow layout is active in stacked widget
        if self.stackedLayout.currentIndex() == 0:

            # get global pos
            pos = self.thumbnail_layout.mapFromGlobal(QCursor.pos())

            # account for scroll bar
            pos.setX(pos.x() + self.thumbnail_layout.horizontalScrollBar().value())
            pos.setY(pos.y() + self.thumbnail_layout.verticalScrollBar().value())

            index = self.flow_layout.indexAt(pos)
            filepaths = [self.version_directories[index]]
        else:
            # get selected rows
            rows = self.list_layout.selectedItems()
            rows = [row.row() for row in rows]
            filepaths = [self.version_directories[row] for row in rows]

        return filepaths


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = DependencyViewer()
    window.show()
    sys.exit(app.exec_())
