try:
    import hou
    from PySide2 import QtWidgets
except Exception as e:
    print(f'hou not found, not running in houdini: {e}')
    from PySide6 import QtWidgets
from apps.pipeDisplay import output_gui
import sys

if __name__ == '__main__':
    application = QtWidgets.QApplication(sys.argv)
    application.setStyle('Fusion')
    window = output_gui.OutputViewer(show_side_bar=True, start_type='Assets', font_scale=1, icon_size=200)
    window.show()
    sys.exit(application.exec())
