"""
QT ui that displays a table of keys and values from a dictionary, with a display of all the values for the selected key.
"""

import sys
import os
import json
import PySide2
import logging

from PySide2 import QtCore, QtWidgets, QtGui
from PySide2.QtWidgets import QApplication, QWidget, QTableWidget, QTableWidgetItem, QVBoxLayout, QHBoxLayout
from PySide2.QtCore import Qt
from core.hutils import logger


class TableWidget(QTableWidget):
    def __init__(self, data, parent=None):
        super(TableWidget, self).__init__(parent)
        self.data = data
        self.initUI()

    def initUI(self):
        self.setColumnCount(2)
        self.setRowCount(len(self.data))
        self.setHorizontalHeaderLabels(['Shot', 'Variant Sets'])
        self.setVerticalHeaderLabels([str(x) for x in self.data.keys()])

        for i, key in enumerate(self.data.keys()):
            # new line for each value
            # self.data[key] = ''.join([str(x) + '\n' for x in self.data[key]])
            print(self.data[key])
            self.setItem(i, 0, QTableWidgetItem(key))
            variants = []
            for k,v in self.data[key].items():
                variants.append('{0}: {1}'.format(k, v))

            text = '\n'.join(variants)
            self.setItem(i, 1, QTableWidgetItem(text))

        self.resizeColumnsToContents()
        self.resizeRowsToContents()

        #resize table
        # resize first column to contents
        self.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
        # set initial size of second column to fit contents
        self.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
        # resize second column to fit window
        self.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)


        self.verticalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)


        # hide vertical header
        self.verticalHeader().setVisible(False)



        # can only select one row at a time
        self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.itemClicked.connect(self.item_click)
        # lock horizontal scroll wheel
        self.horizontalScrollBar().setEnabled(False)


    def item_click(self, item):
        logger.debug(item.text())
        if item.column() == 0:
            logger.debug(item.text())
            logger.debug(self.data[item.text()])


class App(QWidget):
    def __init__(self, data):
        super().__init__()
        self.title = 'PySide2 table example'
        self.left = 10
        self.top = 10
        self.width = 640
        self.height = 400
        self.data = data
        self.initUI()

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        self.table_widget = TableWidget(self.data)
        self.layout = QVBoxLayout()
        self.window_layout = QHBoxLayout()
        self.window_layout.addLayout(self.layout)


        self.setLayout(self.window_layout)

        #add search bar
        self.search_bar = QtWidgets.QLineEdit()
        self.search_bar.setPlaceholderText('Search Variant Sets...')
        #self.search_bar.textChanged.connect(self.search)

        # # refresh search if backspace is pressed
        # self.search_bar.keyPressEvent = self.search_key_press

        # only search when enter is pressed
        self.search_bar.returnPressed.connect(self.search)
        # add search button to search bar
        self.search_button = QtWidgets.QPushButton('Search')
        self.search_button.clicked.connect(self.search)
        self.search_bar_layout = QtWidgets.QHBoxLayout()
        self.search_bar_layout.addWidget(self.search_bar)
        self.search_bar_layout.addWidget(self.search_button)
        self.search_bar_widget = QtWidgets.QWidget()
        self.search_bar_widget.setLayout(self.search_bar_layout)
        self.layout.addWidget(self.search_bar_widget)
        # serach when enter pressed
        self.search_bar.returnPressed.connect(self.search)



        self.layout.addWidget(self.search_bar)
        self.layout.addWidget(self.table_widget)

        # add right click menu to table
        self.table_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table_widget.customContextMenuRequested.connect(self.right_click_menu)

        # add untoggle all right click menu
        self.untoggle_all_action = QtWidgets.QAction('Untoggle All', self)
        self.untoggle_all_action.triggered.connect(self.untoggle_all)

        # add column of key checkboxes to toggle the table
        self.key_checkboxes = QtWidgets.QWidget()
        self.key_checkboxes_layout = QtWidgets.QVBoxLayout()
        self.key_checkboxes.setLayout(self.key_checkboxes_layout)
        self.window_layout.addWidget(self.key_checkboxes)
        self.toggle_keys()
        self.key_checkboxes_layout.setAlignment(Qt.AlignTop)
        self.key_checkboxes_layout.setContentsMargins(0, 0, 0, 0)
        self.key_checkboxes_layout.setSpacing(0)

        # add scroll bar for key checkboxes
        self.key_checkboxes_scroll = QtWidgets.QScrollArea()
        self.key_checkboxes_scroll.setWidget(self.key_checkboxes)
        self.key_checkboxes_scroll.setWidgetResizable(True)
        self.key_checkboxes_scroll.setFixedWidth(200)
        self.window_layout.addWidget(self.key_checkboxes_scroll)





        self.show()

    def search(self, text):
        text = self.search_bar.text()
        # edit variants column to only show the variants that match the search
        for i in range(self.table_widget.rowCount()):
            variants = []
            for k,v in self.data[self.table_widget.item(i, 0).text()].items():
                if text in k:
                    variants.append('{0}: {1}'.format(k, v))
            new_text = '\n'.join(variants)
            self.table_widget.setItem(i, 1, QTableWidgetItem(new_text))

    def right_click_menu(self, pos):
        menu = QtWidgets.QMenu()
        toggle_keys = menu.addAction('Toggle keys')
        toggle_keys.triggered.connect(self.isolate_keys)
        menu.exec_(self.table_widget.mapToGlobal(pos))

    def untoggle_all(self):
        for i in range(self.key_checkboxes_layout.count()):
            self.key_checkboxes_layout.itemAt(i).widget().setChecked(False)

    def toggle_keys(self):
        if self.key_checkboxes.isVisible():
            self.key_checkboxes.hide()
        else:
            self.key_checkboxes.show()
            for i in range(self.table_widget.rowCount()):
                checkbox = QtWidgets.QCheckBox(self.table_widget.item(i, 0).text())
                checkbox.setChecked(True)
                checkbox.stateChanged.connect(self.toggle_key)
                self.key_checkboxes_layout.addWidget(checkbox)

    def toggle_key(self, state):
        sender = self.sender()
        if state == Qt.Checked:
            for i in range(self.table_widget.rowCount()):
                if self.table_widget.item(i, 0).text() == sender.text():
                    self.table_widget.showRow(i)
        else:
            for i in range(self.table_widget.rowCount()):
                if self.table_widget.item(i, 0).text() == sender.text():
                    self.table_widget.hideRow(i)

    def isolate_keys(self):
        # # uncheck checkboxes in key_checkboxes that dont match selected keys
        for i in range(self.table_widget.rowCount()):
            if self.table_widget.item(i, 0).isSelected():
                for j in range(self.key_checkboxes_layout.count()):
                    if self.key_checkboxes_layout.itemAt(j).widget().text() == self.table_widget.item(i, 0).text():
                        self.key_checkboxes_layout.itemAt(j).widget().setChecked(True)
            else:
                for j in range(self.key_checkboxes_layout.count()):
                    if self.key_checkboxes_layout.itemAt(j).widget().text() == self.table_widget.item(i, 0).text():
                        self.key_checkboxes_layout.itemAt(j).widget().setChecked(False)


if __name__ == '__main__':
    app = QApplication(sys.argv)

    test_dict = shots = {
    'shot_01': {
        'variant_set_01': 'merp',
        'variant_set_02': 'variant_b',
        'variant_set_03': 'variant_c'
    },
    'shot_02': {
        'variant_set_01': 'variant_b',
        'variant_set_02': 'variant_a',
        'variant_set_03': 'variant_c'
    },
    'shot_03': {
        'variant_set_01': 'variant_c',
        'variant_set_02': 'variant_b',
        'variant_set_03': 'variant_a'
    },
    'shot_04': {
        'variant_set_01': 'variant_b',
        'variant_set_02': 'variant_c',
        'variant_set_03': 'variant_a'
    },
    'shot_05': {
        'variant_set_01': 'variant_c',
        'variant_set_02': 'variant_a',
        'variant_set_03': 'variant_b'
    },
    'shot_06': {
        'variant_set_01': 'variant_a',
        'variant_set_02': 'variant_c',
        'variant_set_03': 'variant_b'
    },
    'shot_07': {
        'variant_set_01': 'variant_a',
        'variant_set_02': 'variant_b',
        'variant_set_03': 'variant_c'
    },
    'shot_08': {
        'variant_set_01': 'variant_b',
        'variant_set_02': 'w',
        'variant_set_03': 'variant_c'
    },
    'shot_09': {
        'variant_set_01': 'variant_c',
        'variant_set_02': 'x',
        'variant_set_03': 'variant_a'
    },
    'shot_10': {
        'variant_set_01': 'variant_b',
        'variant_set_02': 'p',
        'variant_set_03': 'variant_a'
    }}

    ex = App(test_dict)
    sys.exit(app.exec_())