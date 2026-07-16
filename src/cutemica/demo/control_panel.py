from __future__ import annotations

from PySide6.QtCore import QSignalBlocker, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QGridLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from cutemica.enums import ThemeMode


class ControlPanel(QFrame):
    theme_mode_changed = Signal(object)
    refresh_requested = Signal()
    reset_session_requested = Signal()
    export_report_requested = Signal()

    def __init__(
        self, wallpaper_description: str, parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self.setObjectName("micaControlPanel")
        self.setFixedWidth(500)
        self.setMinimumHeight(500)

        title = QLabel("CuteMica Mac Tester")
        title.setObjectName("panelTitle")
        subtitle = QLabel(
            "This material is generated from your current macOS wallpaper. "
            "No wallpaper image is included in the test report."
        )
        subtitle.setWordWrap(True)

        instructions = QLabel(
            "1. Drag this window around and slowly across both monitors.\n"
            "2. Switch macOS between Light and Dark appearance.\n"
            "3. Change the desktop wallpaper and wait a few seconds.\n"
            "4. Save the test report and send the ZIP file back."
        )
        instructions.setObjectName("testInstructions")
        instructions.setWordWrap(True)

        self._theme = QComboBox()
        self._theme.addItem("Follow system", ThemeMode.AUTO)
        self._theme.addItem("Light", ThemeMode.LIGHT)
        self._theme.addItem("Dark", ThemeMode.DARK)

        refresh = QPushButton("Regenerate material")
        reset = QPushButton("Start a fresh test")
        export = QPushButton("Save test report to Downloads")
        export.setObjectName("exportReport")
        self._status = QLabel("Waiting for first material generation")
        self._status.setWordWrap(True)
        self._test_status = QLabel("Moves 0 · waiting for test activity")
        self._test_status.setWordWrap(True)
        self._export_status = QLabel("")
        self._export_status.setWordWrap(True)
        self._environment = QLabel(wallpaper_description)
        self._environment.setWordWrap(True)

        choices = QGridLayout()
        choices.addWidget(QLabel("Theme"), 0, 0)
        choices.addWidget(self._theme, 0, 1)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 22, 24, 22)
        layout.setSpacing(14)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addWidget(instructions)
        layout.addSpacing(6)
        layout.addLayout(choices)
        layout.addWidget(refresh)
        layout.addWidget(reset)
        layout.addWidget(export)
        layout.addSpacing(4)
        layout.addWidget(self._status)
        layout.addWidget(self._test_status)
        layout.addWidget(self._export_status)
        layout.addWidget(self._environment)

        self._theme.currentIndexChanged.connect(self._publish_theme)
        refresh.clicked.connect(self.refresh_requested)
        reset.clicked.connect(self.reset_session_requested)
        export.clicked.connect(self.export_report_requested)

    def set_generation_status(self, message: str) -> None:
        self._status.setText(message)

    def set_environment_description(self, description: str) -> None:
        self._environment.setText(description)

    def set_test_status(self, message: str) -> None:
        self._test_status.setText(message)

    def set_export_status(self, message: str) -> None:
        self._export_status.setText(message)

    def select_theme_mode(self, mode: ThemeMode) -> None:
        index = self._theme.findData(mode)
        if index < 0 or index == self._theme.currentIndex():
            return
        blocker = QSignalBlocker(self._theme)
        self._theme.setCurrentIndex(index)
        del blocker

    def set_theme_style(self, *, dark: bool) -> None:
        self.setStyleSheet(_DARK_STYLE if dark else _LIGHT_STYLE)

    def _publish_theme(self) -> None:
        mode = self._theme.currentData()
        if isinstance(mode, ThemeMode):
            self.theme_mode_changed.emit(mode)


_LIGHT_STYLE = """
QFrame#micaControlPanel {
    background: rgba(255, 255, 255, 222);
    border: 1px solid rgba(0, 0, 0, 30);
    border-radius: 12px;
    color: #151515;
}
QFrame#micaControlPanel QLabel { color: #151515; }
QLabel#panelTitle { font-size: 20px; font-weight: 600; }
QLabel#testInstructions { line-height: 1.25; }
QComboBox, QPushButton {
    min-height: 30px;
    padding: 0 10px;
    background: rgba(255, 255, 255, 210);
    border: 1px solid rgba(0, 0, 0, 45);
    border-radius: 5px;
}
QPushButton#exportReport { font-weight: 600; }
"""

_DARK_STYLE = """
QFrame#micaControlPanel {
    background: rgba(35, 35, 35, 232);
    border: 1px solid rgba(255, 255, 255, 32);
    border-radius: 12px;
    color: #f3f3f3;
}
QFrame#micaControlPanel QLabel { color: #f3f3f3; }
QLabel#panelTitle { font-size: 20px; font-weight: 600; }
QLabel#testInstructions { line-height: 1.25; }
QComboBox, QPushButton {
    min-height: 30px;
    padding: 0 10px;
    color: #f3f3f3;
    background: rgba(62, 62, 62, 230);
    border: 1px solid rgba(255, 255, 255, 45);
    border-radius: 5px;
}
QPushButton#exportReport { font-weight: 600; }
QComboBox QAbstractItemView { color: #f3f3f3; background: #303030; }
"""
