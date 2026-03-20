import sys
if sys.version_info <= (3, 8):
    from PySide2 import QtWidgets, QtCore
else:
    from PySide6 import QtWidgets, QtCore
from collections import OrderedDict

from hpipe.apps.pipeManager import manager_utils


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


class MultipleTagWidget(QtWidgets.QWidget):
    """
    Renders a row of tag badge buttons for a shot.
    """
    def __init__(self, tags, parent=None):
        super(MultipleTagWidget, self).__init__(parent)
        layout = QtWidgets.QHBoxLayout(self)
        layout.setAlignment(QtCore.Qt.AlignLeft)  # type: ignore
        layout.setContentsMargins(0, 0, 0, 0)

        ordered_tags = OrderedDict(manager_utils.Constants.TAGS)
        main_tags = [t for t in tags if t in ordered_tags]
        additional_tags = [t for t in tags if t not in ordered_tags]

        for tag in main_tags:
            if tag and tag != '':
                layout.addWidget(manager_utils.create_tag_button(tag))

        for tag in additional_tags:
            if tag and tag != '' and tag != ["None"]:
                layout.addWidget(manager_utils.create_tag_button(tag))
