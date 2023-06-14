"""
Project Overview Panel where I can see and edit all projects and shots. This is a project management tool and not a viewer.
"""

# TODO clean up the imports
import sys
import json
import os
from PySide2 import QtWidgets, QtCore, QtGui
from PySide2.QtWidgets import *
import sys
from utility import logger
from PySide2.QtGui import QPixmap
from PySide2.QtCore import QThread, Signal
from collections import OrderedDict
from core import db, project, shot
import datetime


def _load_json_data(json_file):
    """
    Get data from json file
    :return:
    """
    # check if json file exists
    if not os.path.isfile(json_file):
        _log('JSON file not found: {}'.format(json_file))
        return False
    with open(json_file) as data_file:
        data = json.load(data_file)

    return data


def _save_json_data(filepath, old_json, data):
    """
    Save data to json file
    :param data:
    :return:
    """
    # check if json file exists
    if not os.path.isfile(filepath):
        _log('JSON file not found: {}'.format(filepath))
        # if in the same directory as old_json, create the file
        if os.path.dirname(filepath) == os.path.dirname(old_json):
            with open(filepath, 'w') as outfile:
                json.dump(data, outfile, indent=4)
            return True

    with open(filepath, 'w') as outfile:
        json.dump(data, outfile, indent=4)

    return True

def _get_latest_version(filepath):
    """
    Get the latest version of a file
    :param filepath:
    :return:
    """
    import re
    if not os.path.isfile(filepath):
        _log('File not found: {}'.format(filepath))
        return False

    # get all versions of the file
    versions = []
    for file in os.listdir(os.path.dirname(filepath)):
        _log(os.path.basename(file))
        # get basename before version number
        basename = os.path.basename(file).split('_')[:-1]
        basename = '_'.join(basename)
        if basename in file:
            versions.append(file)

    _log(versions)

    # get the latest version
    latest_version = sorted(versions)[-1]

    # full path to latest version
    latest_version = os.path.join(os.path.dirname(filepath), latest_version)

    # get the version number
    match = re.search(r'^(.*?)(_?)(\d+)', filepath)
    if match:
        file_name = match.group(1)
        separator = match.group(2)
        version = int(match.group(3))
        incremented_version = version + 1
        # same padding as version number
        incremented_version = str(incremented_version).zfill(len(match.group(3)))
        incremented_file_path = f"{file_name}{separator}{incremented_version}.json"
        # full path to incremented version
        incremented_file_path = os.path.join(os.path.dirname(filepath), incremented_file_path)

    _log(latest_version)
    _log(incremented_file_path)
    _log(version)

    return (latest_version, incremented_file_path, version)


def _log(message, level='debug'):
    """
    Log a message to the console
    :param message:
    :return:
    """
    logger.warning(message)
    return True


class Constants():
    """
    Constants for the project overview
    """
    from utility import path as util_path
    TEMP_JSON_PATH = util_path.convertPath("Y:/project_db/projects_test_01.json")


class EditableDelegate(QtWidgets.QStyledItemDelegate):
    """
    A delegate that allows the user to edit the text of an item in a QTreeView.
    """
    def createEditor(self, parent, option, index):
        editor = QtWidgets.QLineEdit(parent)
        return editor

    def setEditorData(self, editor, index):
        value = index.model().data(index, QtCore.Qt.DisplayRole)
        editor.setText(value)

    def setModelData(self, editor, model, index):
        value = editor.text()
        model.setData(index, value, QtCore.Qt.EditRole)


class JsonViewer(QtWidgets.QWidget):
    """
    Project Overview Panel where I can see and edit all projects and shots. This is a project management tool and not a viewer.
    """
    def __init__(self, parent=None):
        super(JsonViewer, self).__init__(parent)

    # get data from json file
        # TODO make this a function

        self.database = {}

        # create main layout
        self.main_layout = QHBoxLayout()

        # set stylistic properties
        self.setWindowTitle('Json Viewer')
        self.resize(1920, 1080)
        self.setWindowOpacity(0.99)

    # CREATE MAIN TREE VIEW
        self.tree = QtWidgets.QTreeWidget()
        self.tree.setColumnCount(4)
        self.tree.setHeaderHidden(False)
        self.tree.setFont(QtGui.QFont("Arial", 15, QtGui.QFont.Bold))

        # self.refresh_tree()

        # set various style parms
        self.tree.header().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
        self.tree.header().setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
        self.tree.setAlternatingRowColors(True)
        self.tree.setStyleSheet("alternate-background-color: rgb(60, 60, 60);")
        self.tree.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.tree.setUniformRowHeights(True)

        # Make colors dark
        self.setStyleSheet("background-color: rgb(50, 50, 50); color: rgb(200, 200, 200);")

        delegate = EditableDelegate()
        self.tree.setItemDelegate(delegate)

        # # print out changed data
        # self.tree.itemChanged.connect(self.getUpdateItems)

        # add right click menu
        self.tree.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.open_menu)



    # MAKE BUTTON LAYOUT
        self.button_layout = QVBoxLayout()
        self.button_layout.setSpacing(10)

        # add file path line edit
        # self.file_path_line_edit = QtWidgets.QLineEdit()
        # self.button_layout.addWidget(self.file_path_line_edit)
        # self.file_path_line_edit.setFixedHeight(40)
        # self.file_path_line_edit.setFixedWidth(200)
        # self.file_path_line_edit.setFont(QtGui.QFont("Arial", 12, QtGui.QFont.Bold))
        # self.file_path_line_edit.setText("Y:/project_db/projects_test.json")

        # add show combo box with label
        self.show_label = QtWidgets.QLabel("Show")
        self.button_layout.addWidget(self.show_label)
        self.show_label.setFixedHeight(40)
        self.show_label.setFixedWidth(200)
        self.show_label.setFont(QtGui.QFont("Arial", 12, QtGui.QFont.Bold))
        self.show_combo_box = QtWidgets.QComboBox()
        self.button_layout.addWidget(self.show_combo_box)
        self.show_combo_box.setFixedHeight(40)
        self.show_combo_box.setFixedWidth(200)
        self.show_combo_box.setFont(QtGui.QFont("Arial", 12, QtGui.QFont.Bold))

        # add seq combo box with label
        # self.seq_label = QtWidgets.QLabel("Seq")
        # self.button_layout.addWidget(self.seq_label)
        # self.seq_label.setFixedHeight(40)
        # self.seq_label.setFixedWidth(200)
        # self.seq_label.setFont(QtGui.QFont("Arial", 12, QtGui.QFont.Bold))
        # self.seq_combo_box = QtWidgets.QComboBox()
        # self.button_layout.addWidget(self.seq_combo_box)
        # self.seq_combo_box.setFixedHeight(40)
        # self.seq_combo_box.setFixedWidth(200)
        # self.seq_combo_box.setFont(QtGui.QFont("Arial", 12, QtGui.QFont.Bold))

        # add task qline edit with label
        self.task_label = QtWidgets.QLabel("Task")
        self.button_layout.addWidget(self.task_label)
        self.task_label.setFixedHeight(40)
        self.task_label.setFixedWidth(200)
        self.task_label.setFont(QtGui.QFont("Arial", 12, QtGui.QFont.Bold))
        self.task_line_edit = QtWidgets.QLineEdit()
        self.button_layout.addWidget(self.task_line_edit)
        self.task_line_edit.setFixedHeight(40)
        self.task_line_edit.setFixedWidth(200)
        self.task_line_edit.setFont(QtGui.QFont("Arial", 12, QtGui.QFont.Bold))


        # add refresh button
        self.refresh_button = QtWidgets.QPushButton('Refresh')
        self.refresh_button.clicked.connect(self.refresh)
        self.button_layout.addWidget(self.refresh_button)
        self.refresh_button.setFixedHeight(40)
        self.refresh_button.setFixedWidth(200)
        self.refresh_button.setFont(QtGui.QFont("Arial", 12, QtGui.QFont.Bold))

        # add version up and save button
        self.version_up_button = QtWidgets.QPushButton('Save and Increment')
        self.version_up_button.clicked.connect(self.save)
        self.button_layout.addWidget(self.version_up_button)
        self.version_up_button.setFixedHeight(40)
        self.version_up_button.setFixedWidth(200)
        self.version_up_button.setFont(QtGui.QFont("Arial", 12, QtGui.QFont.Bold))

        # set buttons to all be a fixed size
        self.button_layout.setAlignment(QtCore.Qt.AlignTop)


    # ADD WIDGETS TO LAYOUT
        self.main_layout.addWidget(self.tree)
        self.main_layout.addLayout(self.button_layout)
        self.setLayout(self.main_layout)

# UPDATE UI
    def refresh_tree(self):
        """
        Refresh the tree
        :return:
        """

        self.tree.clear()
        data = _load_json_data(self.json_path)
        self.data = data
        self.populate_tree(data, self.tree.invisibleRootItem())

        # make project titles red
        for i in range(self.tree.topLevelItemCount()):
            self.tree.topLevelItem(i).setForeground(0, QtGui.QColor(255, 150, 0))
            self.tree.topLevelItem(i).setForeground(1, QtGui.QColor(255, 150, 0))


        return True

    def populate_tree(self, data, parent):
        """
        Recursively populate the tree with data from the json file
        :param data:
        :param parent:
        :return:
        """

        for key, value in iter(data.items()):
            # check if date is older than 6 months
            # convert string value to dictionary
            if isinstance(value, dict):
                if value.get('date'):
                    date = value.get('date')
                    date = datetime.datetime.strptime(date, '%Y-%m-%d')
                    six_months_ago = datetime.datetime.now() - datetime.timedelta(days=180)
                    if date < six_months_ago:
                        continue

            if isinstance(value, dict):
                # check if project is older than 6 months
                if key == 'project':
                    print('merp')
                item = QtWidgets.QTreeWidgetItem()
                item.setText(0, key)
                parent.addChild(item)
                self.populate_tree(value, item)
            else:
                item = QtWidgets.QTreeWidgetItem()
                item.setText(0, str(key))
                item.setText(1, str(value))
                parent.addChild(item)

                # Set the Qt.ItemIsEditable flag on the child items to make them editable
                item.setFlags(item.flags() | QtCore.Qt.ItemIsEditable)

# ACTIONS

    def refresh(self):
        """
        Refresh the tree
        :return:
        """
        json = self.find_json()
        self.json_path = json
        self.refresh_tree()
        _log("Refreshed tree")
        _log("JSON path: %s" % json)
        return

    def save(self):
        """
        Save the json file
        :return:
        """
        data = self.tree_contents()
        next_version = _get_latest_version(self.json_path)[1]
        _log("Saving json file: %s" % next_version)
        _save_json_data(next_version, self.json_path, data)
        self.json_path = next_version
        self.refresh()
        _log("Saved json file")
        # update header to file name
        self.header_label.setText(os.path.basename(self.json_path))
        return

    def open_menu(self):
        # Get the selected item(s) from the tree view
        indexes = self.tree.selectedIndexes()
        if not indexes:
            return

        # Get the top-level selected index
        top_index = indexes[0]

        # Traverse the tree to locate the parent item
        while top_index.parent().isValid():
            top_index = top_index.parent()

        # Create the context menu
        menu = QMenu(self.tree)

        # Create the menu action for adding a new key with an empty value
        add_action = QAction("Add Key", self)
        add_action.triggered.connect(lambda: self.add_empty_key(top_index, indexes[0]))  # Pass the top-level index and the selected index
        menu.addAction(add_action)

        # Show the context menu at the right-click position
        menu.exec_(self.tree.mapToGlobal(self.tree.viewport().mapFromGlobal(QtGui.QCursor.pos())))

    def add_empty_key(self, top_index, selected_index):

        # add new key under selected index
        selected_item = self.tree.itemFromIndex(selected_index)
        top_item = self.tree.itemFromIndex(top_index)
        # create new key qtreewidgetitem
        new_key = QtWidgets.QTreeWidgetItem()
        new_key.setText(0, "New Key")
        new_key.setText(1, "")
        # add new key to tree
        selected_item.addChild(new_key)
        # make new key editable
        new_key.setFlags(new_key.flags() | QtCore.Qt.ItemIsEditable)



        # add new key under selected item
        data = self.tree_contents()


        # # Get the JSON data
        # data = self.tree_contents()
        # selected_item = self.tree.itemFromIndex(selected_index)
        # top_item = self.tree.itemFromIndex(top_index)
        #
        # print(selected_item)
        # print(top_item)
        # print(data)
        #
        # # Traverse the tree to locate the item in the JSON hierarchy
        # for index in range(top_item.childCount()):
        #     child_item = top_item.child(index)
        #     if child_item == selected_item:
        #         # Found the item, so add a new key
        #         data[child_item.text(0)]["New Key"] = ""
        #         # Update the tree with the new data
        #         self.populate_tree(data, top_item)
        #         break
        #
        #
        # # Expand the item to show the newly added key
        # # self.tree.expand(selected_index)


# UTILITY FUNCTIONS
    def getUpdateItems(self):
        data = self.tree_contents()
        d1 = data
        d2 = db.Db().data
        self.findDiff(d1, d2)

    def findDiff(self, d1, d2, path=''):
        """
        Find difference between two dictionaries
        :param d1:
        :param d2:
        :param path:
        :return:
        """
        try:
            # get current data from active tree
            for k in d1:
                if k in d2:
                    if type(d1[k]) is dict:
                        self.findDiff(d1[k], d2[k], "[%s/%s]" % (path, k) if path else k)
                        continue
                    if str(d1[k]) != str(d2[k]):
                        result = ["%s: " % path, " DB %s : %s -->" % (k, d2[k]), " TXT %s : %s" % (k, d1[k])]
                        logger.warning(" ".join(result))
                else:
                    logger.info("%s%s as key not in DB\n" % ("%s: " % path if path else "", k))
        except Exception as e:
            logger.error(e)

    def tree_contents(self):
        """
        Get the contents of the tree
        :return:
        """
        data = {}
        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            data[item.text(0)] = self.get_children(item)

        return data

    def get_children(self, item):
        """
        Get the children of the given item
        :param item:
        :return:
        """
        data = {}
        for i in range(item.childCount()):
            child = item.child(i)
            if child.childCount() > 0:
                data[child.text(0)] = self.get_children(child)
            else:
                data[child.text(0)] = child.text(1)
        return data

    def find_json(self):
        # show = self.show_combo.currentText()
        # seq = self.seq_combo.currentText()
        # task = self.task_combo.currentText()
        # root = 'Y:/_pipe'
        # path = os.path.join(root, show, seq, task, 'data.json')
        # temp
        path = _get_latest_version(Constants.TEMP_JSON_PATH)[0]
        return path

    def expend_selected(self):
        selected = self.tree.selectedItems()
        for item in selected:
            self.tree.expandItem(item)

    def collapse_selected(self):
        selected = self.tree.selectedItems()
        for item in selected:
            self.tree.collapseItem(item)

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    sys.path.append('Y:/_pipe')
    window = JsonViewer()
    window.show()
    sys.exit(app.exec_())