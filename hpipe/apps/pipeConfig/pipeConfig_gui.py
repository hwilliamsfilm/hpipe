"""
Pipe Config GUI for configuring pipeline settings.
Supports both standalone (PySide6) and in-Houdini (PySide2) modes.
"""
try:
    import hou
    from PySide2 import QtWidgets, QtCore, QtGui
except Exception:
    from PySide6 import QtWidgets, QtCore, QtGui

from hpipe.core import data_manager
from hpipe.apps import style
from hpipe.core.hutils import logger

log = logger.setup_logger()
log.debug("pipeConfig_gui.py loaded")


# ---------------------------------------------------------------------------
# Config option widgets
# ---------------------------------------------------------------------------

class FileChooser(QtWidgets.QWidget):
    """Browse for a single file."""
    def __init__(self, parent=None, label='', default_path='',
                 description_font=None, label_font=None, return_directory=False):
        super().__init__(parent)
        self.return_directory = return_directory
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.label = QtWidgets.QLabel(label)
        if label_font:
            self.label.setFont(label_font)
        self.label.setFixedWidth(220)
        self.filepath = QtWidgets.QLineEdit()
        if description_font:
            self.filepath.setFont(description_font)
        self.filepath.setReadOnly(True)
        self.filepath.setFrame(False)
        self.filepath.setFocusPolicy(QtCore.Qt.NoFocus)  # type: ignore
        if default_path:
            self.filepath.setText(default_path)
        else:
            self.filepath.setPlaceholderText("Select a file…")
        self.filepath_button = QtWidgets.QPushButton("…")
        self.filepath_button.setFixedWidth(32)
        self.filepath_button.clicked.connect(self.file_dialog)
        layout.addWidget(self.label)
        layout.addWidget(self.filepath, stretch=1)
        layout.addWidget(self.filepath_button)

    def file_dialog(self):
        if self.return_directory:
            path = QtWidgets.QFileDialog.getExistingDirectory(self, "Open Directory", "")
        else:
            path = QtWidgets.QFileDialog.getOpenFileName(self, "Open File", "")[0]
        if path:
            self.filepath.setText(path)


class DirectoryChooser(QtWidgets.QWidget):
    """Browse for a directory."""
    def __init__(self, parent=None, label='', default_path='',
                 description_font=None, label_font=None):
        super().__init__(parent)
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.label = QtWidgets.QLabel(label)
        if label_font:
            self.label.setFont(label_font)
        self.label.setFixedWidth(220)
        self.filepath = QtWidgets.QLineEdit()
        if description_font:
            self.filepath.setFont(description_font)
        self.filepath.setReadOnly(True)
        self.filepath.setFrame(False)
        self.filepath.setFocusPolicy(QtCore.Qt.NoFocus)  # type: ignore
        if default_path:
            self.filepath.setText(default_path)
        else:
            self.filepath.setPlaceholderText("Select a directory…")
        self.filepath_button = QtWidgets.QPushButton("…")
        self.filepath_button.setFixedWidth(32)
        self.filepath_button.clicked.connect(self.file_dialog)
        layout.addWidget(self.label)
        layout.addWidget(self.filepath, stretch=1)
        layout.addWidget(self.filepath_button)

    def file_dialog(self):
        path = QtWidgets.QFileDialog.getExistingDirectory(self, "Open Directory", "")
        if path:
            self.filepath.setText(path + "/")


class Switch(QtWidgets.QWidget):
    """Boolean toggle (True / False)."""
    def __init__(self, parent=None, label='', default=True,
                 description_font=None, label_font=None):
        super().__init__(parent)
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.label = QtWidgets.QLabel(label)
        if label_font:
            self.label.setFont(label_font)
        self.label.setFixedWidth(220)
        self.switch = QtWidgets.QCheckBox()
        if description_font:
            self.switch.setFont(description_font)
        checked = default if isinstance(default, bool) else (default == "True")
        self.switch.setChecked(checked)
        layout.addWidget(self.label)
        layout.addWidget(self.switch)
        layout.addStretch()


class TextOption(QtWidgets.QWidget):
    """Free-text field."""
    def __init__(self, parent=None, label='', default='',
                 description_font=None, label_font=None):
        super().__init__(parent)
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.label = QtWidgets.QLabel(label)
        if label_font:
            self.label.setFont(label_font)
        self.label.setFixedWidth(220)
        self.text = QtWidgets.QLineEdit()
        if description_font:
            self.text.setFont(description_font)
        self.text.setText(default)
        layout.addWidget(self.label)
        layout.addWidget(self.text, stretch=1)


# ---------------------------------------------------------------------------
# Main widget
# ---------------------------------------------------------------------------

class PipeConfig(QtWidgets.QWidget):
    """
    Pipeline configuration panel.
    Reads all config keys from ConfigDataManager and renders an appropriate
    input widget for each one.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(style.WINDOW_STYLE)
        self.setWindowTitle("Pipe Config")
        self.resize(int(1920 / 2), int(1080 / 2))
        self.setWindowIcon(QtGui.QIcon(style.icon_path("film.png")))

        _lbl_font = style.label_font()
        _desc_font = style.small_font()

        # ── Header ─────────────────────────────────────────────────────────
        title_layout = QtWidgets.QHBoxLayout()
        icon_label = QtWidgets.QLabel()
        icon_label.setFixedSize(36, 36)
        icon_pix = QtGui.QPixmap(style.icon_path("film.png"))
        icon_label.setPixmap(icon_pix.scaled(36, 36, QtCore.Qt.KeepAspectRatio,  # type: ignore
                                             QtCore.Qt.SmoothTransformation))  # type: ignore
        title_label = QtWidgets.QLabel("Pipe Config")
        title_label.setFont(style.title_font())
        title_layout.addWidget(icon_label)
        title_layout.addWidget(title_label)
        title_layout.addStretch()

        # ── Options area (scrollable) ───────────────────────────────────────
        self.information_layout = QtWidgets.QVBoxLayout()
        self.information_layout.setSpacing(8)
        self.information_layout.setAlignment(QtCore.Qt.AlignTop)  # type: ignore

        config_dictionary = data_manager.ConfigDataManager().get_all_config()

        for option, default in config_dictionary.items():
            log.debug(f"option: {option}, default: {default}")
            widget: QtWidgets.QWidget
            if default in ("True", "False"):
                widget = Switch(label=option, default=default,
                                label_font=_lbl_font, description_font=_desc_font)
            elif "/" in default or "\\" in default:
                if default.endswith("/") or default.endswith("\\"):
                    widget = DirectoryChooser(label=option, default_path=default,
                                             label_font=_lbl_font, description_font=_desc_font)
                else:
                    widget = FileChooser(label=option, default_path=default,
                                        label_font=_lbl_font, description_font=_desc_font,
                                        return_directory=False)
            else:
                widget = TextOption(label=option, default=default,
                                    label_font=_lbl_font, description_font=_desc_font)
            self.information_layout.addWidget(widget)

        options_container = QtWidgets.QWidget()
        options_container.setLayout(self.information_layout)
        scroll_area = QtWidgets.QScrollArea()
        scroll_area.setWidget(options_container)
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QtWidgets.QFrame.NoFrame)

        # ── Buttons ────────────────────────────────────────────────────────
        self.save_button = QtWidgets.QPushButton("Save and Exit")
        self.save_button.setStyleSheet(style.ACCENT_BUTTON_STYLE)
        self.save_button.setFont(style.button_font())
        self.save_button.setFixedHeight(36)
        self.cancel_button = QtWidgets.QPushButton("Cancel")
        self.cancel_button.setFont(style.button_font())
        self.cancel_button.setFixedHeight(36)

        button_row = QtWidgets.QHBoxLayout()
        button_row.addStretch()
        button_row.addWidget(self.cancel_button)
        button_row.addWidget(self.save_button)

        self.save_button.clicked.connect(self.save_config)
        self.cancel_button.clicked.connect(self.close)

        # ── Main layout ────────────────────────────────────────────────────
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(10)
        main_layout.addLayout(title_layout)
        main_layout.addWidget(_hline())
        main_layout.addWidget(scroll_area, stretch=1)
        main_layout.addWidget(_hline())
        main_layout.addLayout(button_row)

        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding,  # type: ignore
                           QtWidgets.QSizePolicy.Expanding)  # type: ignore

    def save_config(self):
        config_dm = data_manager.ConfigDataManager()
        for i in range(self.information_layout.count()):
            option = self.information_layout.itemAt(i).widget()
            if option is None:
                continue
            if isinstance(option, Switch):
                config_dm.set_config(option.label.text(), str(option.switch.isChecked()))
            elif isinstance(option, (FileChooser, DirectoryChooser)):
                config_dm.set_config(option.label.text(), option.filepath.text())
            elif isinstance(option, TextOption):
                config_dm.set_config(option.label.text(), option.text.text())
        self.close()


def _hline() -> QtWidgets.QFrame:
    line = QtWidgets.QFrame()
    line.setFrameShape(QtWidgets.QFrame.HLine)
    line.setFrameShadow(QtWidgets.QFrame.Sunken)
    return line
