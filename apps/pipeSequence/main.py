from apps.pipeSequence import output_gui
from PySide6 import QtWidgets
import sys

if __name__ == '__main__':
    application = QtWidgets.QApplication(sys.argv)
    application.setStyle('Fusion')
    window = output_gui.SequenceUSDViewer()
    window.show()
    sys.exit(application.exec())
