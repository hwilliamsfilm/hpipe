"""
Pipe Manager GUI for managing projects, shots, and assets.
"""
try:
    import hou
    from PySide2 import QtWidgets, QtCore, QtGui
except Exception as e:
    print(f'hou not found, not running in houdini: {e}')
    from PySide6 import QtWidgets, QtCore, QtGui

import core.constants
from core import data_manager
from core.hutils import logger
import os

log = logger.setup_logger()
log.debug("pipeConfig_gui.py loaded")


class FileChooser(QtWidgets.QWidget):
    """
    File chooser widget that allows the user to select a file or directory.
    """
    def __init__(self,
                 parent=None,
                 label='',
                 default_path='',
                 description_font=None,
                 label_font=None,
                 return_directory=False):

        super(FileChooser, self).__init__(parent)
        self.return_directory = return_directory
        self.main_layout = QtWidgets.QHBoxLayout()
        self.label = QtWidgets.QLabel(label)
        self.label.setFont(label_font)
        self.filepath = QtWidgets.QLineEdit()
        self.filepath.setFont(description_font)
        self.filepath.setReadOnly(True)
        self.filepath.setFrame(False)
        self.filepath.setFocusPolicy(QtCore.Qt.NoFocus)
        if default_path:
            self.filepath.setText(default_path)
        else:
            self.filepath.setPlaceholderText('Select a file or directory')
        self.filepath_button = QtWidgets.QPushButton('...')
        self.filepath_button.clicked.connect(self.file_dialog)
        self.main_layout.addWidget(self.label)
        self.main_layout.addWidget(self.filepath)
        self.main_layout.addWidget(self.filepath_button)
        self.setLayout(self.main_layout)

    def file_dialog(self):
        """
        Opens a file dialog and sets the filepath to the selected file.
        """
        if self.return_directory:
            filepath = QtWidgets.QFileDialog.getExistingDirectory(self, 'Open Directory', '')
        else:
            filepath = QtWidgets.QFileDialog.getOpenFileName(self, 'Open File', '')[0]
        if filepath != '':
            self.filepath.setText(filepath)


class DirectoryChooser(QtWidgets.QWidget):
    """
    Directory chooser widget that allows the user to select a directory.
    """
    def __init__(self, parent=None, label='', default_path='', description_font=None, label_font=None):
        super(DirectoryChooser, self).__init__(parent)
        self.main_layout = QtWidgets.QHBoxLayout()
        self.label = QtWidgets.QLabel(label)
        self.label.setFont(label_font)
        self.filepath = QtWidgets.QLineEdit()
        self.filepath.setFont(description_font)
        self.filepath.setReadOnly(True)
        self.filepath.setFrame(False)
        self.filepath.setFocusPolicy(QtCore.Qt.NoFocus)

        if default_path:
            self.filepath.setText(default_path)
        else:
            self.filepath.setPlaceholderText('Select a directory')

        self.filepath_button = QtWidgets.QPushButton('...')
        self.filepath_button.clicked.connect(self.file_dialog)
        self.main_layout.addWidget(self.label)
        self.main_layout.addWidget(self.filepath)
        self.main_layout.addWidget(self.filepath_button)
        self.setLayout(self.main_layout)

    def file_dialog(self):
        """
        Opens a file dialog and sets the filepath to the selected file.
        """
        filepath = QtWidgets.QFileDialog.getExistingDirectory(self, 'Open Directory', '')
        if filepath != '':
            self.filepath.setText(filepath + '/')


class Switch(QtWidgets.QWidget):
    """
    Switch widget that allows the user to switch between two True or False states.
    """
    def __init__(self, parent=None,
                 label='',
                 default=True,
                 description_font=None,
                 label_font=None):

        super(Switch, self).__init__(parent)
        self.main_layout = QtWidgets.QHBoxLayout()
        self.label = QtWidgets.QLabel(label)
        self.switch = QtWidgets.QCheckBox()
        if default == 'True':
            default = True
        elif default == 'False':
            default = False
        self.switch.setChecked(default)
        self.main_layout.addWidget(self.label)
        self.main_layout.addWidget(self.switch)
        self.setLayout(self.main_layout)
        self.label.setFont(label_font)
        self.switch.setFont(description_font)


class TextOption(QtWidgets.QWidget):
    """
    Text option widget that allows the user to enter text.
    """
    def __init__(self, parent=None, label='', default='', description_font=None, label_font=None):
        super(TextOption, self).__init__(parent)
        self.main_layout = QtWidgets.QHBoxLayout()
        self.label = QtWidgets.QLabel(label)
        self.text = QtWidgets.QLineEdit()
        self.text.setText(default)
        self.main_layout.addWidget(self.label)
        self.main_layout.addWidget(self.text)
        self.setLayout(self.main_layout)
        self.label.setFont(label_font)
        self.text.setFont(description_font)


class PipeConfig(QtWidgets.QWidget):
    """
    Project Overview Panel where I can see and edit all projects and shots. This is a project management tool
    and not a viewer.
    """
    def __init__(self, parent=None):
        super(PipeConfig, self).__init__(parent)

        self.button_font = QtGui.QFont("Helvetica", 15, QtGui.QFont.Bold)
        self.label_font = QtGui.QFont("Helvetica", 20, QtGui.QFont.Bold)
        self.description_font = QtGui.QFont("Helvetica", 15, QtGui.QFont.Light)
        self.tree_font = QtGui.QFont("Helvetica", 25)
        self.title_font = QtGui.QFont("Helvetica", 40, QtGui.QFont.Bold)
        self.title_font.setItalic(True)
        self.watermark_font = QtGui.QFont("Helvetica", 20, QtGui.QFont.Light)
        self.shot_color = QtGui.QColor(60, 110, 200)
        self.project_color = QtGui.QColor(200, 110, 60)
        self.button_stylesheet = "background-color: rgb(80, 90, 100); color: rgb(200, 200, 200)"
        self.window_stylesheet = "background-color: rgb(60, 60, 60); color: rgb(200, 200, 200);"
        self.row_height = 200
        self.alternating_color_stylesheet = "background-color: rgb(65, 65, 65); " \
                                            "alternate-background-color: rgb(55, 55, 55);"
        self.tree_stylesheet = "QTreeView::item { padding: 20px };"

        # Spacer
        self.spacer = QtWidgets.QLineEdit()
        self.spacer.setReadOnly(True)
        self.spacer.setVisible(True)
        self.spacer.setFrame(False)
        self.spacer.setStyleSheet(self.window_stylesheet)
        self.spacer.setFocusPolicy(QtCore.Qt.NoFocus)
        self.spacer_layout = QtWidgets.QVBoxLayout()
        self.spacer_layout.addWidget(self.spacer)

        # Create main title
        self.title_layout = QtWidgets.QHBoxLayout()
        self.title_label = QtWidgets.QLabel('Pipe Config')
        self.icon = QtWidgets.QLabel()
        self.icon.setFixedSize(50, 50)
        self.icon_pixmap = QtGui.QPixmap('../../icons/film.png')
        self.icon_pixmap = self.icon_pixmap.scaled(self.icon.size(), QtCore.Qt.KeepAspectRatio)
        self.icon.setPixmap(self.icon_pixmap)
        self.title_layout.addWidget(self.icon)
        self.title_label.setFont(self.title_font)
        self.title_label.setStyleSheet("color: rgb(200, 200, 200)")
        self.title_layout.addWidget(self.title_label)
        self.title_layout.addStretch()

        # Create information layout
        self.information_layout = QtWidgets.QVBoxLayout()
        self.information_layout.setAlignment(QtCore.Qt.AlignTop)

        self.config_dictionary = data_manager.ConfigDataManager().get_all_config()

        for option, default in self.config_dictionary.items():
            log.debug(f'option: {option}, default: {default}')

            if 'True' in default or 'False' in default:
                path = Switch(label=option,
                              default=default,
                              label_font=self.label_font,
                              description_font=self.description_font)

            elif '/' in default or '\\' in default:

                if default.endswith('/') or default.endswith('\\'):
                    path = DirectoryChooser(label=option,
                                            default_path=default,
                                            label_font=self.label_font,
                                            description_font=self.description_font)

                else:
                    path = FileChooser(label=option,
                                       default_path=default,
                                       label_font=self.label_font,
                                       description_font=self.description_font,
                                       return_directory=False)

            else:
                path = TextOption(label=option,
                                  default=default,
                                  label_font=self.label_font,
                                  description_font=self.description_font)

            self.information_layout.addWidget(path)

        # Create bottom buttons
        self.button_layout = QtWidgets.QHBoxLayout()
        self.save_button = QtWidgets.QPushButton('Save and Exit')
        self.save_button.setFont(self.button_font)
        self.cancel_button = QtWidgets.QPushButton('Cancel')
        self.cancel_button.setFont(self.button_font)
        self.button_layout.addWidget(self.save_button)
        self.button_layout.addWidget(self.cancel_button)

        self.save_button.clicked.connect(self.save_config)
        self.cancel_button.clicked.connect(self.cancel)

        self.main_layout = QtWidgets.QVBoxLayout()
        self.tree_button_layout = QtWidgets.QHBoxLayout()
        self.setWindowIcon(QtGui.QIcon(self.icon_pixmap))

        self.main_layout.addLayout(self.title_layout)
        self.main_layout.addLayout(self.spacer_layout)
        self.main_layout.addLayout(self.information_layout)
        self.main_layout.addLayout(self.button_layout)
        self.main_layout.addLayout(self.tree_button_layout)

        self.setLayout(self.main_layout)
        self.setWindowTitle('Pipe Config')
        self.resize(int(1920/2), int(1080/2))
        self.setWindowOpacity(0.99)
        self.setStyleSheet(self.window_stylesheet)
        self.database = data_manager.ProjectDataManager()

        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

        self.setLayout(self.main_layout)

        # Watermark
        self.watermark_label = QtWidgets.QLabel('2024')
        self.watermark_label.setFont(self.watermark_font)
        self.watermark_label.setStyleSheet("color: rgb(200, 200, 200)")
        self.watermark_label.setAlignment(QtCore.Qt.AlignBottom | QtCore.Qt.AlignRight)
        self.main_layout.addWidget(self.watermark_label)

    def save_config(self):
        """
        Saves the config.
        """
        log.debug('Saving config...')
        config_data_manager = data_manager.ConfigDataManager()
        gui_options = []
        for i in range(self.information_layout.count()):
            gui_options.append(self.information_layout.itemAt(i).widget())
        log.debug(f'gui_options: {gui_options}')
        for option in gui_options:
            if isinstance(option, Switch):
                log.debug(f'SAVING OPTION: {option.label.text()}, WITH VALUE: {str(option.switch.isChecked())}')
                config_data_manager.set_config(option.label.text(), str(option.switch.isChecked()))
            elif isinstance(option, FileChooser):
                log.debug(f'SAVING OPTION: {option.label.text()}, WITH VALUE: {option.filepath.text()}')
                config_data_manager.set_config(option.label.text(), option.filepath.text())
            elif isinstance(option, TextOption):
                log.debug(f'SAVING OPTION: {option.label.text()}, WITH VALUE: {option.text.text()}')
                config_data_manager.set_config(option.label.text(), option.text.text())
        self.close()

    def cancel(self):
        """
        Closes the window.
        """
        self.close()
