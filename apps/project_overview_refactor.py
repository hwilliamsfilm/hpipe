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


def _get_db_data():
    """
    Get data from json file
    :return:
    """
    database = db.Db()
    data = database.data

    # sort tree by project date
    data = OrderedDict(sorted(data.items(), key=lambda t: t[1]['date'], reverse=True))

    return data


def _save_db_data(data):
    """
    Save data to json file
    :param data:
    :return:
    """
    db.Db().dump(data)
    return True


def _add_project(project_name):
    """
    Add a project to the json file
    :param data:
    :param project_name:
    :return:
    """
    # get date
    date = datetime.datetime.now().strftime('%Y-%m-%d')

    # create project object
    proj = project.Project(project_name, date=date)

    # add project to data
    db.Db().add_project(proj)

    return True


def _add_shot(project_name, shot_name):
    """
    Add a shot to the json file
    :param data:
    :param project_name:
    :param shot_name:
    :return:
    """
    # create shot object
    new_shot = shot.Shot(shot_name)

    # add shot to data
    db.Db().add_shot(project_name, new_shot)

    return True


def _log(message, level='debug'):
    """
    Log a message to the console
    :param message:
    :return:
    """
    logger.warning(message)
    return True

def _remove_shot(project_name, shot_name):
    """
    Remove a shot from the json file
    :param data:
    :param project_name:
    :param shot_name:
    :return:
    """
    db.Db().remove_shot(project_name, shot_name)
    return True

def _remove_project(project_name):
    """
    Remove a project from the json file
    :param data:
    :param project_name:
    :return:
    """
    db.Db().remove_project(project_name)
    return True

def _add_shot_tags(project_name, shot_name, tags):
    """
    Add tags to a shot
    :param project_name:
    :param shot_name:
    :param tags:
    :return:
    """
    _log(tags)
    db.Db().add_shot_tags(project_name, shot_name, tags)
    return True

def _remove_shot_tags(project_name, shot_name):
    """
    Remove tags from a shot
    :param project_name:
    :param shot_name:
    :param tags:
    :return:
    """
    db.Db().remove_all_tags(project_name, shot_name)
    return True

def _create_tag_button(tag):
    # add button for each tag to column 3
    button = QtWidgets.QPushButton(tag)
    _log(tag)
    # set button color using constants.TAGS
    if tag in Constants.TAGS:
        button.setStyleSheet("border-radius: 5px; background-color: %s; color: %s" % (Constants.TAGS[tag]["color"], Constants.TAGS[tag]["text_color"]))
    else:
        button.setStyleSheet("border-radius: 5px; background-color: %s; color: %s" % (Constants.TAGS["other"]["color"], Constants.TAGS["other"]["text_color"]))
    # set button size to fit row
    button.setFixedWidth(80)
    button.setFixedHeight(30)
    # set text font
    button.setFont(QtGui.QFont("Arial", 8, QtGui.QFont.Bold))
    return button


class Constants():
    """
    Constants for the project overview
    """
    TAGS = {
        "ingested": {"color": "#0000FF", "text_color": "black"},
        "tracked": {"color": "#FFA500", "text_color": "black"},
        "first look": {"color": "#00FF00", "text_color": "black"},
        "final": {"color": "#FF0000", "text_color": "black"},
        "delivered": {"color": "#000000", "text_color": "white"},
        "maybe": {"color": "#000000", "text_color": "white"},
        "other": {"color": "#ADD8E6", "text_color": "black"},
        "ACTIVE": {"color": "#00FF00", "text_color": "black"},
    }


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


class MultipleTagWidget(QWidget):
    """
    Represents multiple buttons in a widget
    """
    def __init__(self, tags, parent=None):
        super(MultipleTagWidget,self).__init__(parent)
        self.layout = QHBoxLayout()
        # right align layout contents
        self.layout.setAlignment(QtCore.Qt.AlignLeft)
        self.layout.setContentsMargins(0, 0, 0, 0)

        ordered_tags = OrderedDict(Constants.TAGS)
        main_tags = []
        additional_tags = []
        for tag in tags:
            if tag in ordered_tags:
                main_tags.append(tag)
            else:
                additional_tags.append(tag)

        _log(tags)
        for tag in main_tags:
            if tag is not None:
                if tag is not '':
                    button = _create_tag_button(tag)
                    # button has rounded corners
                    # button.setStyleSheet("border-radius: 5px")
                    self.layout.addWidget(button)
        for tag in additional_tags:
            if tag is not None:
                if tag is not '':
                    if tag is not ["None"]:
                        button = _create_tag_button(tag)
                        # button has rounded corners
                        # button.setStyleSheet("border-radius: 5px")
                        self.layout.addWidget(button)

        # for tag in additional_tags:
        #     if tag is not None:
        #         if tag is not '':
        #             button = _create_tag_button(tag)
        #             # button has rounded corners
        #             # button.setStyleSheet("border-radius: 5px")
        #             self.layout.addWidget(button)

        self.setLayout(self.layout)


class ProjectOverview(QtWidgets.QWidget):
    """
    Project Overview Panel where I can see and edit all projects and shots. This is a project management tool and not a viewer.
    """
    def __init__(self, parent=None):
        super(ProjectOverview, self).__init__(parent)

    # get data from json file
        # TODO make this a function

        self.database = {}

        # create main layout
        self.main_layout = QHBoxLayout()

        # set stylistic properties
        self.setWindowTitle('Project Overview Panel')
        self.resize(1920, 1080)
        self.setWindowOpacity(0.99)

    # CREATE MAIN TREE VIEW
        self.tree = QtWidgets.QTreeWidget()
        self.tree.setColumnCount(4)
        self.tree.setHeaderHidden(False)
        self.tree.setFont(QtGui.QFont("Arial", 15, QtGui.QFont.Bold))

        self.refresh_tree()

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

        # print out changed data
        self.tree.itemChanged.connect(self.getUpdateItems)


    # MAKE BUTTON LAYOUT
        self.button_layout = QVBoxLayout()
        self.button_layout.setSpacing(10)

        # add add shot button
        self.add_shot_button = QtWidgets.QPushButton('Add Shot')
        self.add_shot_button.clicked.connect(self.add_shot)
        self.button_layout.addWidget(self.add_shot_button)
        self.add_shot_button.setFixedHeight(40)
        self.add_shot_button.setFixedWidth(200)
        self.add_shot_button.setFont(QtGui.QFont("Arial", 12, QtGui.QFont.Bold))

        # add add project button
        self.add_project_button = QtWidgets.QPushButton('Add Project')
        self.add_project_button.clicked.connect(self.add_project)
        self.button_layout.addWidget(self.add_project_button)
        # set font
        self.add_project_button.setFont(QtGui.QFont("Arial", 12, QtGui.QFont.Bold))
        # rezie button to fixed size
        self.add_project_button.setFixedHeight(40)
        self.add_project_button.setFixedWidth(200)

        # add shot tags
        self.add_shot_tags_button = QtWidgets.QPushButton('Add Shot Tags')
        self.add_shot_tags_button.clicked.connect(self.add_shot_tags)
        self.button_layout.addWidget(self.add_shot_tags_button)
        self.add_shot_tags_button.setFixedHeight(40)
        self.add_shot_tags_button.setFixedWidth(200)
        self.add_shot_tags_button.setFont(QtGui.QFont("Arial", 12, QtGui.QFont.Bold))

        # remove all shot tags
        self.remove_shot_tags_button = QtWidgets.QPushButton('Remove Shot Tags')
        self.remove_shot_tags_button.clicked.connect(self.remove_shot_tags)
        self.button_layout.addWidget(self.remove_shot_tags_button)
        self.remove_shot_tags_button.setFixedHeight(40)
        self.remove_shot_tags_button.setFixedWidth(200)
        self.remove_shot_tags_button.setFont(QtGui.QFont("Arial", 12, QtGui.QFont.Bold))

        # add save button
        self.save_button = QtWidgets.QPushButton('Save')
        self.save_button.clicked.connect(self.save)
        self.button_layout.addWidget(self.save_button)
        self.save_button.setFixedHeight(40)
        self.save_button.setFixedWidth(200)
        self.save_button.setFont(QtGui.QFont("Arial", 12, QtGui.QFont.Bold))

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
        # get project names that are expanded
        expanded_projects = []
        expanded_shots = []
        for i in range(self.tree.topLevelItemCount()):
            if self.tree.topLevelItem(i).isExpanded():
                expanded_projects.append(self.tree.topLevelItem(i).text(0))
                for k in range(self.tree.topLevelItem(i).childCount()):
                    for j in range(self.tree.topLevelItem(i).child(k).childCount()):
                        if self.tree.topLevelItem(i).child(k).isExpanded():
                            expanded_shots.append(self.tree.topLevelItem(i).child(k).text(0))

        self.tree.clear()
        data = _get_db_data()
        self.database = db.Db()
        self.populate_tree(data, self.tree.invisibleRootItem())

        # make project titles red
        for i in range(self.tree.topLevelItemCount()):
            self.tree.topLevelItem(i).setForeground(0, QtGui.QColor(255, 150, 0))
            self.tree.topLevelItem(i).setForeground(1, QtGui.QColor(255, 150, 0))

        # make all shots blue
        for i in range(self.tree.topLevelItemCount()):
            for j in range(self.tree.topLevelItem(i).childCount()):
                for k in range(self.tree.topLevelItem(i).child(j).childCount()):
                    self.tree.topLevelItem(i).child(j).child(k).setForeground(0, QtGui.QColor(0, 150, 255))
                    self.tree.topLevelItem(i).child(j).child(k).setForeground(1, QtGui.QColor(0, 150, 255))
                    # get project
                    project = self.tree.topLevelItem(i).text(0)
                    _log(project)
                    # get shot tags for each shot
                    shot = self.tree.topLevelItem(i).child(j).child(k).text(0)
                    shot_tags = self.database.get_project(project).get_shot(shot).get_tags()
                    if shot_tags is not None and shot_tags is not ['']:
                        print(shot_tags)
                        button = MultipleTagWidget(shot_tags)
                        self.tree.setItemWidget(self.tree.topLevelItem(i).child(j).child(k), 3, button)



        # expand projects that were expanded before
        for i in range(self.tree.topLevelItemCount()):
            if self.tree.topLevelItem(i).text(0) in expanded_projects:
                self.tree.topLevelItem(i).setExpanded(True)
                for j in range(self.tree.topLevelItem(i).childCount()):
                    if self.tree.topLevelItem(i).child(j).text(0) in expanded_shots:
                        self.tree.topLevelItem(i).child(j).setExpanded(True)


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

    def add_shot(self):
        """
        Add a shot to the selected project
        :return:
        """
        # get selected project
        selected = self.tree.selectedItems()
        # check to see if a project is selected
        if selected:
            # check to see if the selected item is a project
            if selected[0].parent():
                # check to see if the selected item is a shot
                if selected[0].parent().parent():
                    # if the selected item is a shot, get the parent of the parent
                    selected = selected[0].parent().parent()
                else:
                    # if the selected item is a sequence, get the parent
                    selected = selected[0].parent()
            else:
                # if the selected item is a project, get the selected item
                selected = selected[0]

        _log('Adding shot to project: {}'.format(selected.text(0)), 'info')

        # ask user for a shot name
        shot_name, ok = QtWidgets.QInputDialog.getText(self, 'Add Shot', 'Enter shot name:')
        if ok:
            # add shot to json file
            _log('Adding shot: {}'.format(shot_name), 'info')
            _add_shot(selected.text(0), shot_name)

            # refresh the tree
            self.refresh_tree()
        return True

    def add_project(self):
        """
        Add a project to the json file
        :return:
        """
        # ask user for a project name
        project_name, ok = QtWidgets.QInputDialog.getText(self, 'Add Project', 'Enter project name:')
        if ok:
            # add project to json file
            _log('Adding project: {}'.format(project_name), 'info')
            _add_project(project_name)

            # refresh the tree
            self.refresh_tree()
        return True

    def remove_project(self):
        """
        Remove a project from the json file
        :return:
        """
        # get selected project
        selected = self.tree.selectedItems()
        # check to see if a project is selected
        if selected:
            # check to see if the selected item is a project
            if selected[0].parent():
                # if the selected item is a sequence, get the parent
                selected = selected[0].parent()
            else:
                # if the selected item is a project, get the selected item
                selected = selected[0]

        _log('Removing project: {}'.format(selected.text(0)), 'info')

        # remove project from json file
        _remove_project(selected.text(0))

        # refresh the tree
        self.refresh_tree()
        return True

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

    def save(self):
        """
        Save the data to the database
        :return:
        """
        new_database = db.Db()
        db_data = new_database.data
        tree_data = self.tree_contents()
        self.findDiff(tree_data, db_data)
        new_database.backup_db()
        new_database.dump(tree_data)
        self.refresh_tree()

    def add_shot_tags(self):
        # get selected shot
        selected = self.tree.selectedItems()
        # check to see if a shot is selected

        selected_projects = []
        selected_shots = []

        if selected:
            # check to see if the selected item is a shot
            for item in selected:
                if item.parent():
                    # check to see if the selected item is a shot
                    if item.parent().parent():
                        # if the selected item is a shot, get the parent of the parent
                        selected_projects.append(item.parent().parent().text(0))
                        selected_shots.append(item.text(0))
                    else:
                        # if the selected item is a sequence, get the parent
                        return
                else:
                    # if the selected item is a project, get the selected item
                    return

        # popup a dialog to get the tags separated by commas
        tags, ok = QtWidgets.QInputDialog.getText(self, 'Add Tags', 'Enter tags separated by commas:')

        if ok:
        # add tags to json file
            for p, s in zip(selected_projects, selected_shots):
                s = s.replace(' ', '')
                _add_shot_tags(p, s, tags)

        # refresh the tree
        self.refresh_tree()

    def remove_shot_tags(self):
        # get selected shot
        selected = self.tree.selectedItems()
        # check to see if a shot is selected

        selected_projects = []
        selected_shots = []

        if selected:
            # check to see if the selected item is a shot
            for item in selected:
                if item.parent():
                    # check to see if the selected item is a shot
                    if item.parent().parent():
                        # if the selected item is a shot, get the parent of the parent
                        selected_projects.append(item.parent().parent().text(0))
                        selected_shots.append(item.text(0))
                        # set the tags child to None
                        item.child(4).setText(1, None)
                    else:
                        # if the selected item is a sequence, get the parent
                        return
                else:
                    # if the selected item is a project, get the selected item
                    return

        for p, s in zip(selected_projects, selected_shots):
            s = s.replace(' ', '')
            _remove_shot_tags(p, s)

        # refresh the tree
        self.refresh_tree()



if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    sys.path.append('Y:/_pipe')
    window = ProjectOverview()
    window.show()
    sys.exit(app.exec_())