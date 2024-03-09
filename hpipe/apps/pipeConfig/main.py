try:
    import hou
    from PySide2 import QtWidgets
except Exception as e:
    print(f'hou not found, not running in houdini: {e}')
    from PySide6 import QtWidgets

from hpipe.apps.pipeConfig import pipeConfig_gui
import sys

if __name__ == '__main__':
    application = QtWidgets.QApplication(sys.argv)
    application.setStyle('Fusion')
    window = pipeConfig_gui.PipeConfig()
    window.show()
    sys.exit(application.exec_())
