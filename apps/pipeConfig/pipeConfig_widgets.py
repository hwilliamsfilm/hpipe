try:
    import hou
    from PySide2 import QtWidgets, QtCore
except Exception as e:
    print(f'hou not found, not running in houdini: {e}')
    from PySide6 import QtWidgets, QtCore

from collections import OrderedDict
import pipeConfig_utils


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
    Represents multiple buttons in a widget
    """
    def __init__(self, tags, parent=None):
        super(MultipleTagWidget,self).__init__(parent)
        self.layout = QtWidgets.QHBoxLayout()

        self.layout.setAlignment(QtCore.Qt.AlignLeft)
        self.layout.setContentsMargins(0, 0, 0, 0)

        ordered_tags = OrderedDict(manager_utils.Constants.TAGS)
        main_tags = []
        additional_tags = []
        for tag in tags:
            if tag in ordered_tags:
                main_tags.append(tag)
            else:
                additional_tags.append(tag)

        for tag in main_tags:
            if tag is not None:
                if tag is not '':
                    button = pipeConfig_utils._create_tag_button(tag)
                    self.layout.addWidget(button)
        for tag in additional_tags:
            if tag is not None:
                if tag is not '':
                    if tag is not ["None"]:
                        button = pipeConfig_utils._create_tag_button(tag)
                        self.layout.addWidget(button)

        self.setLayout(self.layout)
