"""
Shared style definitions for all hPipe GUI applications.

Provides a consistent dark theme, font presets, and color palette.
"""

import os
import sys
from datetime import date

if sys.version_info <= (3, 8):
    from PySide2 import QtGui, QtCore
else:
    from PySide6 import QtGui, QtCore

# ---------------------------------------------------------------------------
# Icon helper
# ---------------------------------------------------------------------------
_ICONS_DIR = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'icons')
)


def icon_path(name: str) -> str:
    """Return the absolute path to an icon file in hpipe/icons/."""
    return os.path.join(_ICONS_DIR, name)


# ---------------------------------------------------------------------------
# Colour palette
# ---------------------------------------------------------------------------
BG_DARK = "#1e1e1e"
BG_MID = "#2d2d2d"
BG_LIGHT = "#3c3c3c"
BG_HOVER = "#4a4a4a"
BORDER = "#555555"

TEXT_PRIMARY = "#e8e8e8"
TEXT_SECONDARY = "#a0a0a0"
TEXT_DISABLED = "#606060"

ACCENT_BLUE = "#3d7ab5"
ACCENT_BLUE_HOVER = "#4d8ec8"
ACCENT_ORANGE = "#c86e3c"
ACCENT_GREEN = "#4caf50"
ACCENT_YELLOW = "#f0c040"

PROJECT_COLOR = QtGui.QColor(200, 110, 60)
SHOT_COLOR = QtGui.QColor(80, 140, 210)
TREE_PRIMARY = QtGui.QColor(210, 210, 210)
TREE_SECONDARY = QtGui.QColor(130, 130, 130)
DATE_COLOR = QtGui.QColor(120, 120, 120)

# ---------------------------------------------------------------------------
# Stylesheets
# ---------------------------------------------------------------------------
WINDOW_STYLE = f"""
    QWidget {{
        background-color: {BG_MID};
        color: {TEXT_PRIMARY};
        font-family: "Segoe UI", Helvetica, Arial, sans-serif;
    }}
    QLabel {{
        background-color: transparent;
        color: {TEXT_PRIMARY};
    }}
    QLineEdit, QTextEdit {{
        background-color: {BG_DARK};
        color: {TEXT_PRIMARY};
        border: 1px solid {BORDER};
        border-radius: 4px;
        padding: 4px 8px;
        selection-background-color: {ACCENT_BLUE};
    }}
    QLineEdit:read-only {{
        color: {TEXT_SECONDARY};
    }}
    QLineEdit:focus, QTextEdit:focus {{
        border: 1px solid {ACCENT_BLUE};
    }}
    QComboBox {{
        background-color: {BG_LIGHT};
        color: {TEXT_PRIMARY};
        border: 1px solid {BORDER};
        border-radius: 4px;
        padding: 4px 8px;
        combobox-popup: 0;
    }}
    QComboBox:hover {{
        border: 1px solid {ACCENT_BLUE};
    }}
    QComboBox::drop-down {{
        border: none;
        width: 20px;
    }}
    QComboBox QAbstractItemView {{
        background-color: {BG_LIGHT};
        color: {TEXT_PRIMARY};
        selection-background-color: {ACCENT_BLUE};
        border: 1px solid {BORDER};
    }}
    QPushButton {{
        background-color: {BG_LIGHT};
        color: {TEXT_PRIMARY};
        border: 1px solid {BORDER};
        border-radius: 4px;
        padding: 6px 14px;
        font-weight: 500;
    }}
    QPushButton:hover {{
        background-color: {BG_HOVER};
        border: 1px solid {ACCENT_BLUE};
    }}
    QPushButton:pressed {{
        background-color: {ACCENT_BLUE};
    }}
    QPushButton:disabled {{
        color: {TEXT_DISABLED};
        border: 1px solid {BG_LIGHT};
    }}
    QPushButton:flat {{
        background-color: transparent;
        border: none;
    }}
    QPushButton:flat:hover {{
        background-color: {BG_HOVER};
        border: none;
    }}
    QToolButton {{
        background-color: {BG_LIGHT};
        color: {TEXT_PRIMARY};
        border: 1px solid {BORDER};
        border-radius: 4px;
    }}
    QToolButton:hover {{
        background-color: {BG_HOVER};
        border: 1px solid {ACCENT_BLUE};
    }}
    QToolButton:pressed {{
        background-color: {ACCENT_BLUE};
    }}
    QCheckBox {{
        color: {TEXT_PRIMARY};
        spacing: 6px;
    }}
    QCheckBox::indicator {{
        width: 14px;
        height: 14px;
        border: 1px solid {BORDER};
        border-radius: 3px;
        background-color: {BG_DARK};
    }}
    QCheckBox::indicator:checked {{
        background-color: {ACCENT_BLUE};
        border: 1px solid {ACCENT_BLUE};
    }}
    QSlider::groove:horizontal {{
        height: 4px;
        background: {BG_DARK};
        border-radius: 2px;
    }}
    QSlider::handle:horizontal {{
        background: {ACCENT_BLUE};
        border: none;
        width: 14px;
        height: 14px;
        margin: -5px 0;
        border-radius: 7px;
    }}
    QSlider::sub-page:horizontal {{
        background: {ACCENT_BLUE};
        border-radius: 2px;
    }}
    QScrollArea {{
        border: none;
        background-color: {BG_MID};
    }}
    QScrollBar:vertical {{
        background: {BG_DARK};
        width: 10px;
        border-radius: 5px;
    }}
    QScrollBar::handle:vertical {{
        background: {BG_HOVER};
        border-radius: 5px;
        min-height: 20px;
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}
    QScrollBar:horizontal {{
        background: {BG_DARK};
        height: 10px;
        border-radius: 5px;
    }}
    QScrollBar::handle:horizontal {{
        background: {BG_HOVER};
        border-radius: 5px;
        min-width: 20px;
    }}
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
        width: 0px;
    }}
    QTreeWidget {{
        background-color: {BG_DARK};
        color: {TEXT_PRIMARY};
        border: 1px solid {BORDER};
        alternate-background-color: {BG_MID};
    }}
    QTreeWidget::item {{
        padding: 4px 6px;
    }}
    QTreeWidget::item:selected {{
        background-color: {ACCENT_BLUE};
        color: white;
    }}
    QTreeWidget::item:hover:!selected {{
        background-color: {BG_HOVER};
    }}
    QTableWidget {{
        background-color: {BG_DARK};
        color: {TEXT_PRIMARY};
        border: 1px solid {BORDER};
        gridline-color: {BG_LIGHT};
        alternate-background-color: {BG_MID};
    }}
    QTableWidget::item:selected {{
        background-color: {ACCENT_BLUE};
    }}
    QHeaderView::section {{
        background-color: {BG_LIGHT};
        color: {TEXT_SECONDARY};
        border: none;
        padding: 4px;
    }}
    QProgressBar {{
        background-color: {BG_DARK};
        border: 1px solid {BORDER};
        border-radius: 4px;
        text-align: center;
        color: {TEXT_PRIMARY};
    }}
    QProgressBar::chunk {{
        background-color: {ACCENT_BLUE};
        border-radius: 3px;
    }}
    QMenu {{
        background-color: {BG_LIGHT};
        color: {TEXT_PRIMARY};
        border: 1px solid {BORDER};
    }}
    QMenu::item:selected {{
        background-color: {ACCENT_BLUE};
    }}
    QFrame[frameShape="4"],
    QFrame[frameShape="5"] {{
        color: {BORDER};
    }}
    QDialog {{
        background-color: {BG_MID};
    }}
"""

ACCENT_BUTTON_STYLE = f"""
    QPushButton {{
        background-color: {ACCENT_BLUE};
        color: white;
        border: none;
        border-radius: 4px;
        padding: 6px 14px;
        font-weight: 600;
    }}
    QPushButton:hover {{
        background-color: {ACCENT_BLUE_HOVER};
    }}
    QPushButton:pressed {{
        background-color: {ACCENT_BLUE};
    }}
"""

DANGER_BUTTON_STYLE = f"""
    QPushButton {{
        background-color: #8b2020;
        color: white;
        border: none;
        border-radius: 4px;
        padding: 6px 14px;
        font-weight: 600;
    }}
    QPushButton:hover {{
        background-color: #a83030;
    }}
"""

DRAG_DROP_STYLE = f"""
    QPushButton {{
        background-color: transparent;
        color: {TEXT_SECONDARY};
        border: 2px dashed {BORDER};
        border-radius: 6px;
        font-size: 13px;
    }}
    QPushButton:hover {{
        border-color: {ACCENT_BLUE};
        color: {TEXT_PRIMARY};
    }}
"""

SIDEBAR_LABEL_STYLE = f"color: {TEXT_SECONDARY}; font-size: 11px; font-weight: 600; text-transform: uppercase;"

# ---------------------------------------------------------------------------
# Font presets
# ---------------------------------------------------------------------------
def title_font(scale: float = 1.0) -> QtGui.QFont:
    f = QtGui.QFont("Segoe UI", int(28 * scale), QtGui.QFont.Bold)  # type: ignore
    return f


def subtitle_font(scale: float = 1.0) -> QtGui.QFont:
    f = QtGui.QFont("Segoe UI", int(11 * scale), QtGui.QFont.Light)  # type: ignore
    f.setItalic(True)
    return f


def button_font(scale: float = 1.0) -> QtGui.QFont:
    return QtGui.QFont("Segoe UI", int(10 * scale), QtGui.QFont.Medium)  # type: ignore


def label_font(scale: float = 1.0) -> QtGui.QFont:
    return QtGui.QFont("Segoe UI", int(12 * scale), QtGui.QFont.Bold)  # type: ignore


def small_font(scale: float = 1.0) -> QtGui.QFont:
    return QtGui.QFont("Segoe UI", int(10 * scale))


def tree_font(scale: float = 1.0) -> QtGui.QFont:
    return QtGui.QFont("Segoe UI", int(11 * scale))


def monospace_font(scale: float = 1.0) -> QtGui.QFont:
    return QtGui.QFont("Consolas", int(10 * scale))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def current_year() -> str:
    return str(date.today().year)
