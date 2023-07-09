from package import pipeline_pilot
from PySide2 import QtWidgets, QtCore, QtGui
import sys

if __name__ == '__main__':
    application = QtWidgets.QApplication(sys.argv)
    window = pipeline_pilot.MainView()
    window.show()
    sys.exit(application.exec_())
