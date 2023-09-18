"""
Pipe Manager GUI for viewing outputs, comps, and renders.
"""

import sys
if sys.version_info <= (3, 8):
    from PySide2 import QtWidgets, QtCore, QtGui
    from typing_extensions import TypedDict, Literal, overload
else:
    from PySide6 import QtWidgets, QtCore, QtGui

import core.project
from core import data_manager, project, shot
from apps.pipeManager import pipe_widgets
from apps.pipeManager import manager_utils
from core.hutils import logger
from typing import *

log = logger.setup_logger()
log.debug("output_widgets.py loaded")


class QHLine(QtWidgets.QFrame):
    def __init__(self):
        super(QHLine, self).__init__()
        self.setFrameShape(QtWidgets.QFrame.HLine)
        self.setFrameShadow(QtWidgets.QFrame.Sunken)


class FlowLayout(QtWidgets.QLayout):
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
        """
        Delete the items in the layout.
        """
        item = self.takeAt(0)
        while item:
            item = self.takeAt(0)

    def addItem(self, item):
        """
        Add an item to the layout.
        """
        self.itemList.append(item)

    def count(self):
        """
        Return the number of items in the layout.
        """
        return len(self.itemList)

    def itemAt(self, index):
        """
        Return the item at the given index.
        """
        if 0 <= index < self.count():
            return self.itemList[index]
        return None

    def takeAt(self, index):
        """
        Remove and return the item at the given index.
        """
        if 0 <= index < self.count():
            return self.itemList.pop(index)
        return None

    def expandingDirections(self):
        """
        Return the expanding directions.
        """
        return QtCore.Qt.Orientations(QtCore.Qt.Orientation(0))

    def hasHeightForWidth(self):
        """
        Return True if the layout has a height for width.
        """
        # TODO: figure out what this does
        return True

    def heightForWidth(self, width):
        """
        Return the height for the given width.
        """
        height = self.doLayout(QtCore.QRect(0, 0, width, 0), True)
        return height

    def setGeometry(self, rect):
        """
        Set the geometry of the layout.
        """
        super(FlowLayout, self).setGeometry(rect)
        self.doLayout(rect, False)

    def sizeHint(self):
        """
        Return the size hint.
        """
        return self.minimumSize()

    def minimumSize(self):
        """Return the minimum size."""
        size = QtCore.QSize()

        for item in self.itemList:
            size = size.expandedTo(item.minimumSize())

        margin, _, _, _ = self.getContentsMargins()
        size += QtCore.QSize(2 * margin, 2 * margin)
        size.setWidth(max(size.width(), 50))
        return size

    def doLayout(self, rect, test_only=False):
        """
        Perform the layout.
        :param rect: The rectangle to perform the layout in.
        :param test_only: If True, only test the layout.
        :return: The height of the layout.
        """
        x = rect.x()
        y = rect.y()
        line_height = 0
        for item in self.itemList:
            wid = item.widget()
            spaceX = self.spacing() + wid.style().layoutSpacing(QtWidgets.QSizePolicy.PushButton,  # type: ignore
                                                                QtWidgets.QSizePolicy.PushButton,  # type: ignore
                                                                QtCore.Qt.Horizontal)
            spaceY = self.spacing() + wid.style().layoutSpacing(QtWidgets.QSizePolicy.PushButton,  # type: ignore
                                                                QtWidgets.QSizePolicy.PushButton,  # type: ignore
                                                                QtCore.Qt.Vertical)
            nextX = x + item.sizeHint().width() + spaceX
            if nextX - spaceX > rect.right() and line_height > 0:
                x = rect.x()
                y = y + line_height + spaceY
                nextX = x + item.sizeHint().width() + spaceX
                line_height = 0

            if not test_only:
                item.setGeometry(QtCore.QRect(QtCore.QPoint(x, y), item.sizeHint()))
            x = nextX
            line_height = max(line_height, item.sizeHint().height())
        return y + line_height - rect.y()

    def indexAt(self, pos):
        """
        Return the index of the widget at the given position.
        """
        for i, item in enumerate(self.itemList):
            if item.geometry().contains(pos):
                return i
        return -1

