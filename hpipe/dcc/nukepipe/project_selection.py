"""
This is an extension of the hpipe.apps.pipeManager.main.py file. The purpose of this file is to provide a gui for
selecting a project to save the current nuke script into.
"""

from hpipe.apps.pipeManager import manager_gui
from PySide6 import QtWidgets
import sys

if __name__ == '__main__':
    application = QtWidgets.QApplication(sys.argv)
    application.setStyle('Fusion')
    window = manager_gui.ProjectOverview(sidebar=False, file_dropper=False, commit_selection=True)
    window.show()
    sys.exit(application.exec())
