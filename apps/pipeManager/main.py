from apps.pipeManager import manager_gui
from PySide6 import QtWidgets
import sys

if __name__ == '__main__':
    application = QtWidgets.QApplication(sys.argv)
    application.setStyle('Fusion')
    window = manager_gui.ProjectOverview()
    window.show()
    sys.exit(application.exec())
