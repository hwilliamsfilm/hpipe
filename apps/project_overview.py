# create a GUI that recursively browses through a json file
# and allows you to edit it

import sys
sys.path.append('Y:\\_pipe')

import json
import os
from PySide2 import QtWidgets, QtCore, QtGui
from PySide2.QtWidgets import QMenu, QAction
from core import db as db
from collections import OrderedDict
import datetime
import logging
import sys
from utility import logger
from PySide2.QtGui import QPixmap
from PySide2.QtCore import QThread, Signal

class QTextEditLogger(logging.Handler):
    def __init__(self, parent):
        super().__init__()
        self.widget = QtWidgets.QPlainTextEdit(parent)
        self.widget.setReadOnly(True)

    def emit(self, record):
        msg = self.format(record)
        self.widget.appendPlainText(msg)

class EditableDelegate(QtWidgets.QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        editor = QtWidgets.QLineEdit(parent)
        return editor

    def setEditorData(self, editor, index):
        value = index.model().data(index, QtCore.Qt.DisplayRole)
        editor.setText(value)

    def setModelData(self, editor, model, index):
        value = editor.text()
        model.setData(index, value, QtCore.Qt.EditRole)

class EmittingStream(QtCore.QObject):

    textWritten = QtCore.Signal(str)

    def write(self, text):
        # skip empty lines
        if text.strip() != '':
            # add timestamp to text
            text = str(datetime.datetime.now().strftime('%H:%M:%S')) + ' ' + text
            self.textWritten.emit(' '.join(str(text).splitlines()))

class JsonEditor(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(JsonEditor, self).__init__(parent)

        # Get database
        self.database = db.Db()
        self.data = self.database.data

        # sort tree by project date
        self.data = OrderedDict(sorted(self.data.items(), key=lambda t: t[1]['date'], reverse=True))


        # main layout
        # add vertical layout to the window
        self.pane_layout = QtWidgets.QVBoxLayout()
        self.top_pane = QtWidgets.QHBoxLayout()
        self.bottom_pane = QtWidgets.QHBoxLayout()
        self.pane_layout.addLayout(self.top_pane)
        self.pane_layout.addLayout(self.bottom_pane)
        self.global_layout = QtWidgets.QHBoxLayout()
        self.global_layout.addLayout(self.pane_layout)
        self.setLayout(self.global_layout)

        self.setWindowTitle('PROJECT MANAGER')
        # make window size screen size
        self.resize(1920, 1080)
        self.setWindowOpacity(0.99)
        #self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)

        # create horizontal layout for buttons
        self.button_layout = QtWidgets.QHBoxLayout()
        self.top_pane.addLayout(self.button_layout)

        # TREE 1
        self.tree1()

        # TREE 2
        self.tree2()

        # add last line of python console to the bottom of the window
        self.console = QtWidgets.QPlainTextEdit()
        self.console.setReadOnly(True)
        self.bottom_pane.addWidget(self.console)

        # add image viewer to the bottom of the window
        self.image_viewer = QtWidgets.QGraphicsView()
        self.bottom_pane.addWidget(self.image_viewer)
        scene = QtWidgets.QGraphicsScene()
        self.image_viewer.setScene(scene)
        pixmap = QPixmap(r'Y:\_houdini_\icons\main.png')
        self.pixmap_item = QtWidgets.QGraphicsPixmapItem(pixmap)
        scene.addItem(self.pixmap_item)
        self.image_viewer.setScene(scene)



        # update image viewer when tree2 item is selected
        self.tree2.itemSelectionChanged.connect(self.update_image_viewer)

        #remove scrollbars from image viewer
        self.image_viewer.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.image_viewer.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)


        sys.stdout = EmittingStream()
        sys.stdout.textWritten.connect(self.console.appendPlainText)
        # set console text to green
        self.console.setStyleSheet("color: rgb(0, 255, 0);")

        # if press enter in tree, run function
        self.tree.itemChanged.connect(self.getUpdateItems)

        self.buttons()

        # make buttons top aligned
        self.button_layout.addStretch()




        # make highlight color brighter
        self.setStyleSheet("QTreeView::item:selected {background-color: rgb(200, 200, 200);}")

        # make buttons top aligned
        self.button_layout.addStretch()

        # set all font size to 12
        self.setStyleSheet("font-size: 60px;")



    # LAYOUT ELEMENTS
    def tree1(self):
        self.tree = QtWidgets.QTreeWidget()
        self.tree.setColumnCount(2)
        # hide header
        self.tree.setHeaderHidden(True)

        # add tree to main layout
        self.top_pane.addWidget(self.tree)

        self.populate_tree(self.data, self.tree.invisibleRootItem())
        self.tree.setFont(QtGui.QFont("Arial", 15, QtGui.QFont.Bold))

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


        # set various style parms
        self.tree.header().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
        self.tree.setAlternatingRowColors(True)
        self.tree.setStyleSheet("alternate-background-color: rgb(60, 60, 60);")
        self.tree.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.tree.setUniformRowHeights(True)

        # Make colors dark
        self.setStyleSheet("background-color: rgb(50, 50, 50); color: rgb(200, 200, 200);")

        # # add double click action for assets
        # self.tree.itemDoubleClicked.connect(self.open_asset)

        # set right click menu
        # Create context menu
        self.context_menu = QMenu(self)
        self.action1 = QAction("open file browser", self)
        self.action1.triggered.connect(self.open_in_explorer)
        self.context_menu.addAction(self.action1)

        self.tree.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.show_context_menu)

        delegate = EditableDelegate()
        self.tree.setItemDelegate(delegate)

    def tree2(self):
        self.tree2 = QtWidgets.QTreeWidget()
        self.tree2.setColumnCount(3)
        self.tree2.setHeaderHidden(True)

        # add tree2 to main layout
        self.top_pane.addWidget(self.tree2)

        # update tree2 when tree is clicked
        self.tree.itemClicked.connect(self.tree2_contents)

        # create context menu for tree2
        self.context_menu2 = QMenu(self)
        self.action2 = QAction("open in RV", self)
        self.action2.triggered.connect(self.open_asset)
        self.context_menu2.addAction(self.action2)

        # make lines alternate colors
        self.tree2.setAlternatingRowColors(True)
        # set tree 2 select color red
        self.tree2.setStyleSheet("alternate-background-color: rgb(60, 60, 60); QTreeView::item:selected {background-color: rgb(255, 150, 0);}")
        self.tree2.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.tree2.setUniformRowHeights(True)

        # auto resize columns
        self.tree2.header().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
        self.tree2.header().setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)

        # add column lines
        self.tree2.setRootIsDecorated(False)



        self.tree2.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.tree2.customContextMenuRequested.connect(self.show_context_menu2)

    def buttons(self):
        # create buttons on side of window
        self.button_layout = QtWidgets.QVBoxLayout()
        self.global_layout.addLayout(self.button_layout)

        # add button to add a new project
        self.add_project_button = QtWidgets.QPushButton('Add Project')
        self.button_layout.addWidget(self.add_project_button)

        self.add_shot_button = QtWidgets.QPushButton('Add Shot')
        self.button_layout.addWidget(self.add_shot_button)

        self.delivery_button = QtWidgets.QPushButton('Send to Delivery')
        self.button_layout.addWidget(self.delivery_button)

        # add toggle button to show comps
        self.toggle_comp = QtWidgets.QCheckBox('COMPS')
        self.button_layout.addWidget(self.toggle_comp)

        # add toggle button to show plates
        self.toggle_plate = QtWidgets.QCheckBox('PLATES')
        self.button_layout.addWidget(self.toggle_plate)

        # add toggle button to show renders
        self.toggle_renders = QtWidgets.QCheckBox('RENDERS')
        self.button_layout.addWidget(self.toggle_renders)

        # add toggle button to show workarea
        self.toggle_workarea = QtWidgets.QCheckBox('WORKAREA')
        self.button_layout.addWidget(self.toggle_workarea)

        # save tree back to database
        self.save_button = QtWidgets.QPushButton('Save')
        self.button_layout.addWidget(self.save_button)
        self.save_button.clicked.connect(self.save)

        # run tree2 function when toggle button changed
        self.toggle_comp.stateChanged.connect(self.tree2_contents)
        self.toggle_plate.stateChanged.connect(self.tree2_contents)
        self.toggle_renders.stateChanged.connect(self.tree2_contents)
        self.toggle_workarea.stateChanged.connect(self.tree2_contents)

        # set each buttons font size
        self.add_project_button.setStyleSheet("font-size: 20px;")
        self.toggle_comp.setStyleSheet("font-size: 20px;")
        self.toggle_plate.setStyleSheet("font-size: 20px;")
        self.toggle_renders.setStyleSheet("font-size: 20px;")
        self.toggle_workarea.setStyleSheet("font-size: 20px;")
        self.save_button.setStyleSheet("font-size: 20px;")
        self.add_shot_button.setStyleSheet("font-size: 20px;")
        self.delivery_button.setStyleSheet("font-size: 20px;")

    # UTILITIES
    def getSelectedItems(self):
        items = []
        for item in self.tree.selectedItems():
            # get parent item
            parent = item.parent()
            if parent:
                # get top most parent of item
                while parent.parent():
                    parent = parent.parent()

                # get project name
                project_name = parent.text(0)

                # get shot name
                shot_name = item.text(0)

                # get shot object
                shot = self.database.get_project(project_name).get_shot(shot_name, self.database)

                if shot:
                    items.append(shot)

            else:
                # get project name
                project_name = item.text(0)
                # get project object
                print("getting project")
                project = self.database.get_project(project_name)
                if project:
                    items.append(project)

        return items

    def normalOutputWritten(self, text):
        """Append text to the QTextEdit."""

        # add timestamp to beginning of line
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        text = timestamp + " " + text
        self.textEdit.append(' '.join(str(text).splitlines()))
        print(text)
        self.textEdit.ensureCursorVisible()
        self.console.ensureCursorVisible()

    def tree2_contents(self):
        self.tree2.clear()
        assets = []
        db_objects = self.getSelectedItems()

        # check if COMP toggle is checked
        if self.toggle_comp.isChecked():
            for db_object in db_objects:
                if db_object.type == 'shot':
                    for comp in db_object.get_comps(self.database):
                        assets.append(comp)
                elif db_object.type == 'project':
                    for shot in db_object.get_shots():
                        for comp in shot.get_comps(self.database):
                            assets.append(comp)

        # # check if plates toggle is checked
        if self.toggle_plate.isChecked():
            for db_object in db_objects:
                if db_object.type == 'shot':
                    for plate in db_object.get_plates(self.database):
                        assets.append(plate)
                elif db_object.type == 'project':
                    for shot in db_object.get_shots():
                        for plate in shot.get_plates(self.database):
                            assets.append(plate)

        asset_dict = {}
        # set 1st column to asset name, 2nd column to asset path, 3rd column to asset date
        for asset in assets:
            date = asset.get_date().strftime("%Y-%m-%d %H:%M")
            asset_dict[asset.get_filename()] = [asset.get_filename(), asset.get_root(), date]

        # sort by date
        asset_dict = dict(sorted(asset_dict.items(), key=lambda item: item[1][2], reverse=True))

        for asset in asset_dict:
            item = QtWidgets.QTreeWidgetItem(self.tree2)
            item.setText(0, asset_dict[asset][0])
            item.setText(1, asset_dict[asset][1])
            item.setText(2, asset_dict[asset][2])

    def update_image_viewer(self):
        from utility import path
        # get selected item in tree2
        item = self.tree2.selectedItems()[0]

        if not item:
            return

        # get filepath
        filepath = item.text(1)

        if not filepath:
            return

        print(filepath)

        image = path.get_image_sequences(filepath)[0]
        image_filepath = image.filepaths[0]
        print(image_filepath)

        new_pixmap = QPixmap(image_filepath)

        # Set the new pixmap for the QGraphicsPixmapItem object
        self.pixmap_item.setPixmap(new_pixmap)

        # Update the view with the new image
        self.image_viewer.update()
        self.image_viewer.fitInView(self.pixmap_item, QtCore.Qt.KeepAspectRatio)


    # SCRIPTS / ACTIONS
    def open_asset(self):
        # get selected items in tree2
        items = self.tree2.selectedItems()
        paths = []
        for item in items:
            if item:
                filepath = item.text(1)
                if filepath:
                    # open filepath in rv
                    paths.append(filepath)

        # make paths space separated string
        paths = ' '.join(paths)
        try:
            import subprocess
            subprocess.Popen(r'C:\Program Files\ShotGrid\RV-2022.3.1\bin\rv.exe {path}'.format(path=paths))
        except Exception as e:
            print(e)

    def open_in_explorer(self):
        filepaths = []
        # get item object
        item = self.getSelectedItems()
        for i in item:
            if i.type == 'shot':
                filepaths.append(i.get_shot_path())
            elif i.type == 'project':
                filepaths.append(i.get_project_path())

        # open explorer for each filepath
        for filepath in filepaths:
            os.startfile(filepath)

    # MISC
    def show_context_menu(self, pos):
        self.context_menu.exec_(self.tree.viewport().mapToGlobal(pos))

    def show_context_menu2(self, pos):
        self.context_menu2.exec_(self.tree2.viewport().mapToGlobal(pos))

    def populate_tree(self, data, parent):

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

            #self.findDiff(value, self.data, db.Db().data)

    def getUpdateItems(self):
        data = self.tree_contents()
        d1 = data
        d2 = db.Db().data
        self.findDiff(d1, d2)

    def findDiff(self, d1, d2, path=''):
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
        data = {}
        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            data[item.text(0)] = self.get_children(item)

        return data

    def get_children(self, item):
        data = {}
        for i in range(item.childCount()):
            child = item.child(i)
            if child.childCount() > 0:
                data[child.text(0)] = self.get_children(child)
            else:
                data[child.text(0)] = child.text(1)
        return data

    def save(self):
        new_database = db.Db()
        db_data = new_database.data
        tree_data = self.tree_contents()
        self.findDiff(tree_data, db_data)
        new_database.backup_db()
        new_database.dump(tree_data)

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = JsonEditor()
    window.show()
    sys.exit(app.exec_())