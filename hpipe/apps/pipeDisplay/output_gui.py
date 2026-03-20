"""
Pipe Display GUI for viewing outputs, comps, and renders.
"""

import sys
try:
    import hou
    from PySide2 import QtWidgets, QtCore, QtGui
except Exception:
    from PySide6 import QtWidgets, QtCore, QtGui

from hpipe.core import data_manager, project, shot
from hpipe.apps.pipeDisplay import output_widgets, output_utils
from hpipe.apps import style
from hpipe.core.hutils import logger
from typing import *
from hpipe.assets import reviewable
import time

log = logger.setup_logger()
log.debug("output_gui.py loaded")


# ---------------------------------------------------------------------------
# Background worker: scan directories and build the reviewable list
# ---------------------------------------------------------------------------

class ReviewableLoader(QtCore.QThread):
    """
    Fetches the list of Reviewable objects from disk in a background thread so
    the main thread is never blocked by directory scans.

    Emits:
      - ``finished(list)`` — the complete reviewable list once scanning is done.
      - ``error(str)``     — if an exception occurs.
    """
    finished = QtCore.Signal(list)
    error = QtCore.Signal(str)

    def __init__(self, shot_list: Optional[List[shot.Shot]],
                 directory_type: str, filter_text: str):
        super().__init__()
        self._shot_list = shot_list
        self._directory_type = directory_type
        self._filter_text = filter_text

    def run(self):
        try:
            result = output_utils.get_reviewables(
                self._shot_list, self._directory_type, self._filter_text
            )
            self.finished.emit(result or [])
        except Exception as exc:
            log.error(f"ReviewableLoader error: {exc}")
            self.error.emit(str(exc))


# ---------------------------------------------------------------------------
# Background worker: load thumbnails as QImage (safe for non-main threads)
# ---------------------------------------------------------------------------

class ThumbnailLoader(QtCore.QThread):
    """
    Loads thumbnails for each reviewable in a background thread.

    Qt rule: ``QPixmap`` must only be created in the main (GUI) thread.
    We therefore emit ``QImage`` objects — QImage is thread-safe — and let
    the main-thread slot convert them to QPixmap.

    Emits:
      - ``thumbnail_loaded(QImage, int)`` — image + reviewable index.
      - ``progress(int)``                 — 0-100 completion percentage.
    """
    thumbnail_loaded = QtCore.Signal(QtGui.QImage, int)
    progress = QtCore.Signal(int)

    def __init__(self, reviewable_list: List[reviewable.Reviewable],
                 fallback_path: str):
        super().__init__()
        self.reviewable_list = reviewable_list
        self._fallback_path = fallback_path
        self._running = True

    def run(self):
        total = len(self.reviewable_list)
        for index, rev in enumerate(self.reviewable_list):
            if not self._running:
                break
            try:
                image_fp = rev.get_thumbnail_image()
                if image_fp:
                    qimage = QtGui.QImage(image_fp.system_path())
                    if qimage.isNull():
                        raise ValueError("QImage returned null")
                else:
                    raise ValueError("no thumbnail path")
            except Exception:
                qimage = QtGui.QImage(self._fallback_path)

            if self._running:
                self.thumbnail_loaded.emit(qimage, index)
                pct = int((index + 1) / total * 100) if total else 100
                self.progress.emit(pct)

            # brief yield so the main thread can process the signal
            time.sleep(0.001)

    def stop(self):
        self._running = False
        self.requestInterruption()
        self.wait()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _sidebar_label(text: str) -> QtWidgets.QLabel:
    lbl = QtWidgets.QLabel(text)
    lbl.setStyleSheet(style.SIDEBAR_LABEL_STYLE)
    return lbl


# ---------------------------------------------------------------------------
# Main viewer widget
# ---------------------------------------------------------------------------

class OutputViewer(QtWidgets.QDialog):
    """
    Viewer panel for browsing render outputs, comps, and assets.
    All disk I/O runs in background threads — the main thread stays responsive.
    """
    def __init__(self,
                 parent=None,
                 font_scale: float = 1.0,
                 start_project: str = output_utils.Constants.START_PROJECT,
                 show_side_bar: bool = True,
                 start_type: str = "Assets",
                 position: tuple = None,
                 size: tuple = None,
                 icon_size: int = None):
        super(OutputViewer, self).__init__(parent)

        self.setStyleSheet(style.WINDOW_STYLE)
        self.setWindowTitle("Output Viewer")
        self.setWindowIcon(QtGui.QIcon(style.icon_path("germ.png")))

        self.return_value = {}
        self.isDialog = not show_side_bar

        self.database = data_manager.ProjectDataManager()
        self._reviewable_loader: Optional[ReviewableLoader] = None
        self._thumbnail_loader: Optional[ThumbnailLoader] = None
        # Keep the current reviewable list so button click → filepath works.
        self._current_reviewables: List[reviewable.Reviewable] = []

        # ── Header ─────────────────────────────────────────────────────────
        title_layout = QtWidgets.QHBoxLayout()
        icon_label = QtWidgets.QLabel()
        icon_label.setFixedSize(36, 36)
        icon_pix = QtGui.QPixmap(style.icon_path("germ.png"))
        icon_label.setPixmap(icon_pix.scaled(36, 36, QtCore.Qt.KeepAspectRatio,  # type: ignore
                                             QtCore.Qt.SmoothTransformation))  # type: ignore
        title_label = QtWidgets.QLabel("Output Viewer")
        title_label.setFont(style.title_font(font_scale))
        title_layout.addWidget(icon_label)
        title_layout.addWidget(title_label)
        title_layout.addStretch()

        # ── Content area ───────────────────────────────────────────────────
        self.flow_layout = output_widgets.FlowLayout()
        thumb_container = QtWidgets.QWidget()
        thumb_container.setLayout(self.flow_layout)
        self.thumbnail_scroll = QtWidgets.QScrollArea()
        self.thumbnail_scroll.setWidget(thumb_container)
        self.thumbnail_scroll.setWidgetResizable(True)

        self.thumbnail_scroll.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)  # type: ignore
        self.context_menu = QtWidgets.QMenu(self)
        self.open_action = self.context_menu.addAction("Open In Explorer")
        self.open_in_rv_action = self.context_menu.addAction("Open In RV")
        self.move_to_delivery_action = self.context_menu.addAction("Move To Delivery")
        self.thumbnail_scroll.customContextMenuRequested.connect(
            lambda pos: self.context_menu.exec_(self.thumbnail_scroll.mapToGlobal(pos)))

        self.list_layout = QtWidgets.QTableWidget()
        self.list_layout.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)  # type: ignore
        self.list_layout.verticalHeader().setVisible(False)
        self.list_layout.setColumnCount(1)
        self.list_layout.setAlternatingRowColors(True)
        self.list_layout.horizontalHeader().setVisible(False)

        self.stacked = QtWidgets.QStackedWidget()
        self.stacked.addWidget(self.thumbnail_scroll)  # 0 = icon view
        self.stacked.addWidget(self.list_layout)       # 1 = list view

        # ── Sidebar ────────────────────────────────────────────────────────
        self.directory_type = QtWidgets.QComboBox()
        self.show_selection = QtWidgets.QComboBox()
        self.shot_selection = QtWidgets.QComboBox()
        self.sequence_toggle = QtWidgets.QCheckBox("Browse Full Sequence")
        self.latest_version = QtWidgets.QCheckBox("Latest Version Only")

        icon_size_val = icon_size if icon_size else 100
        self.size_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)  # type: ignore
        self.size_slider.setMinimum(50)
        self.size_slider.setMaximum(400)
        self.size_slider.setValue(icon_size_val)
        self.size_slider.setTickInterval(50)
        self.size_slider.setTickPosition(QtWidgets.QSlider.TicksBelow)  # type: ignore

        sidebar_widget = QtWidgets.QWidget()
        sidebar_widget.setFixedWidth(200)
        sidebar_vbox = QtWidgets.QVBoxLayout(sidebar_widget)
        sidebar_vbox.setContentsMargins(8, 8, 8, 8)
        sidebar_vbox.setSpacing(6)
        sidebar_vbox.setAlignment(QtCore.Qt.AlignTop)  # type: ignore

        sidebar_vbox.addWidget(_sidebar_label("TYPE"))
        sidebar_vbox.addWidget(self.directory_type)
        sidebar_vbox.addWidget(output_widgets.QHLine())
        sidebar_vbox.addWidget(_sidebar_label("SHOW"))
        sidebar_vbox.addWidget(self.show_selection)
        sidebar_vbox.addWidget(_sidebar_label("SHOT"))
        sidebar_vbox.addWidget(self.shot_selection)
        sidebar_vbox.addWidget(output_widgets.QHLine())
        sidebar_vbox.addWidget(self.sequence_toggle)
        sidebar_vbox.addWidget(self.latest_version)
        sidebar_vbox.addWidget(output_widgets.QHLine())
        sidebar_vbox.addWidget(_sidebar_label("ICON SIZE"))
        sidebar_vbox.addWidget(self.size_slider)

        # ── Bottom bar ─────────────────────────────────────────────────────
        self.icon_view = QtWidgets.QCheckBox("Icon View")
        self.filter = QtWidgets.QLineEdit()
        self.filter.setPlaceholderText("Filter…")
        self.loading_bar = QtWidgets.QProgressBar()
        self.loading_bar.setRange(0, 100)
        self.loading_bar.setTextVisible(False)
        self.loading_bar.setFixedHeight(6)
        self.loading_bar.setValue(0)

        bottom_bar = QtWidgets.QHBoxLayout()
        bottom_bar.addWidget(self.icon_view)
        bottom_bar.addWidget(self.filter, stretch=1)
        bottom_bar.addWidget(self.loading_bar, stretch=1)

        # ── Body ───────────────────────────────────────────────────────────
        body_layout = QtWidgets.QHBoxLayout()
        body_layout.addWidget(self.stacked, stretch=1)
        if show_side_bar:
            body_layout.addWidget(sidebar_widget)

        # ── Main layout ────────────────────────────────────────────────────
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(8)
        main_layout.addLayout(title_layout)
        main_layout.addLayout(body_layout, stretch=1)
        main_layout.addLayout(bottom_bar)

        w, h = size if size else (1000, 800)
        self.resize(w, h)
        if position:
            self.move(position[0], position[1])

        # ── Populate combos ────────────────────────────────────────────────
        self.directory_type.addItems(output_utils.Constants.DIRECTORY_TYPES.keys())  # type: ignore
        self.show_selection.addItems(output_utils.Constants.SHOWS)  # type: ignore

        # ── Defaults ──────────────────────────────────────────────────────
        self.show_selection.setCurrentText(start_project)
        self.directory_type.setCurrentText(start_type)
        self.sequence_toggle.setChecked(True)
        self.icon_view.setChecked(True)
        self.update_outputs()

        # ── Connections ────────────────────────────────────────────────────
        self.icon_view.toggled.connect(self.change_view)
        self.show_selection.currentTextChanged.connect(self.update_shots)
        self.show_selection.currentIndexChanged.connect(lambda: self.update_combo("show"))
        self.shot_selection.currentIndexChanged.connect(lambda: self.update_combo("shot"))
        self.directory_type.currentIndexChanged.connect(lambda: self.update_combo("type"))
        self.sequence_toggle.toggled.connect(self.update_outputs)
        self.filter.returnPressed.connect(self.update_outputs)
        self.size_slider.valueChanged.connect(self._on_size_changed)

    # ── Slots ─────────────────────────────────────────────────────────────

    def update_shots(self) -> bool:
        self.shot_selection.clear()
        self.shot_selection.addItems(
            output_utils.shots_from_show(self.show_selection.currentText()))
        return True

    def change_view(self):
        self.stacked.setCurrentIndex(0 if self.icon_view.isChecked() else 1)

    def update_combo(self, combo_type: Optional[str] = None) -> bool:
        current_project = self.show_selection.currentText()
        if combo_type == "show":
            self.shot_selection.clear()
            self.shot_selection.addItems(
                output_utils.shots_from_show(current_project, database=self.database))
        elif combo_type in ("shot", "type"):
            self.update_outputs()
        return True

    def update_outputs(self) -> bool:
        """
        Start a background scan for reviewables.  The UI is not blocked.
        """
        self._stop_all_workers()
        self.clear_flow_layout()
        self.clear_list_layout()
        self._current_reviewables = []
        self.loading_bar.setValue(0)

        self._reviewable_loader = ReviewableLoader(
            self.current_shots(),
            self.directory_type.currentText(),
            self.filter.text(),
        )
        self._reviewable_loader.finished.connect(self._on_reviewables_ready)
        self._reviewable_loader.error.connect(
            lambda msg: log.error(f"ReviewableLoader: {msg}"))
        self._reviewable_loader.start()
        return True

    def _on_reviewables_ready(self, output_reviewables: List[reviewable.Reviewable]):
        """Called in the main thread once the directory scan is complete."""
        self._current_reviewables = output_reviewables
        log.debug(f"Reviewables ready: {output_reviewables}")

        self.update_flow_layout(output_reviewables)
        self.update_list_layout(output_reviewables)

        if not output_reviewables:
            self.loading_bar.setValue(100)
            return

        fallback = output_utils.Constants.TEMP_IMAGE.system_path()
        self._thumbnail_loader = ThumbnailLoader(output_reviewables, fallback)
        self._thumbnail_loader.thumbnail_loaded.connect(self._on_thumbnail_ready)
        self._thumbnail_loader.progress.connect(self.loading_bar.setValue)
        self._thumbnail_loader.start()

    def _on_thumbnail_ready(self, qimage: QtGui.QImage, index: int):
        """
        Receives a QImage from the background thread and converts it to a
        QPixmap here in the main thread (the only thread where QPixmap is safe).
        """
        try:
            button = self.flow_layout.itemAt(index).widget()
            if button:
                pixmap = QtGui.QPixmap.fromImage(qimage)
                button.setIcon(QtGui.QIcon(pixmap))
        except (AttributeError, TypeError):
            pass

    def _on_size_changed(self):
        """Resize existing buttons in-place without re-scanning disk."""
        size = self.size_slider.value()
        for i in range(self.flow_layout.count()):
            btn = self.flow_layout.itemAt(i).widget()
            if btn:
                btn.setIconSize(QtCore.QSize(int(size / 1.2), size))  # type: ignore
                btn.setFixedSize(size, size + 20)
                font = btn.font()
                font.setPointSize(max(7, int(size / 25)))
                btn.setFont(font)

    # ── Data accessors ─────────────────────────────────────────────────────

    def current_show(self) -> project.Project:
        return self.database.get_project(self.show_selection.currentText())

    def current_shots(self) -> Optional[List[shot.Shot]]:
        project_instance = self.database.get_project(self.show_selection.currentText())
        if not project_instance:
            return None
        if self.sequence_toggle.isChecked():
            return project_instance.get_shots()
        return [project_instance.get_shot(self.shot_selection.currentText())]

    # ── Layout helpers ─────────────────────────────────────────────────────

    def clear_flow_layout(self) -> bool:
        for i in reversed(range(self.flow_layout.count())):
            widget = self.flow_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        return True

    def clear_list_layout(self) -> bool:
        self.list_layout.clearContents()
        self.list_layout.setRowCount(0)
        return True

    def update_flow_layout(self, output_reviewables: List[reviewable.Reviewable]) -> bool:
        if not output_reviewables:
            return False
        size = self.size_slider.value()
        fallback_pixmap = QtGui.QPixmap(output_utils.Constants.TEMP_IMAGE.system_path())
        for rev in output_reviewables:
            button = QtWidgets.QToolButton()
            button.setText(rev.asset_name)
            button.setIcon(QtGui.QIcon(fallback_pixmap))
            button.setIconSize(QtCore.QSize(int(size / 1.2), size))  # type: ignore
            button.setToolButtonStyle(QtCore.Qt.ToolButtonTextUnderIcon)  # type: ignore
            font = button.font()
            font.setPointSize(max(7, int(size / 25)))
            button.setFont(font)
            button.setFixedSize(size, size + 20)
            button.setToolTip(rev.asset_name)
            if self.isDialog:
                button.clicked.connect(self._on_button_clicked)
            self.flow_layout.addWidget(button)
        return True

    def update_list_layout(self, output_reviewables: List[reviewable.Reviewable]) -> bool:
        if not output_reviewables:
            return False
        self.list_layout.setRowCount(len(output_reviewables))
        for count, rev in enumerate(output_reviewables):
            self.list_layout.setItem(count, 0, QtWidgets.QTableWidgetItem(rev.asset_name))
        return True

    # ── Worker lifecycle ───────────────────────────────────────────────────

    def _stop_all_workers(self):
        for worker in (self._thumbnail_loader, self._reviewable_loader):
            if worker and worker.isRunning():
                try:
                    worker.stop()
                except AttributeError:
                    worker.requestInterruption()
                    worker.wait()

    # ── Dialog exit ────────────────────────────────────────────────────────

    def _on_button_clicked(self):
        sender = self.sender()
        self._stop_all_workers()
        if sender:
            self.return_value["filepath"] = sender.text()
            self.accept()

    def exit(self) -> str:
        self._on_button_clicked()
        return self.return_value.get("filepath", "")

    def closeEvent(self, event):
        self._stop_all_workers()
        super().closeEvent(event)
