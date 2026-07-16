from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from cutemica.demo.progress_panel import ProgressPanel
from cutemica.diagnostics.session import ValidationProgress


class ControlPanel(QFrame):
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

        self._progress = ProgressPanel()
        reset = QPushButton("Start a fresh test")
        export = QPushButton("Save test report to Downloads")
        export.setObjectName("exportReport")
        self._status = QLabel("Waiting for first material generation")
        self._status.setWordWrap(True)
        self._export_status = QLabel("")
        self._export_status.setWordWrap(True)
        self._environment = QLabel(wallpaper_description)
        self._environment.setWordWrap(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 22, 24, 22)
        layout.setSpacing(14)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addWidget(self._progress)
        layout.addSpacing(6)
        layout.addWidget(reset)
        layout.addWidget(export)
        layout.addSpacing(4)
        layout.addWidget(self._status)
        layout.addWidget(self._export_status)
        layout.addWidget(self._environment)

        reset.clicked.connect(self.reset_session_requested)
        export.clicked.connect(self.export_report_requested)

    def set_generation_status(self, message: str) -> None:
        self._status.setText(message)

    def set_environment_description(self, description: str) -> None:
        self._environment.setText(description)

    def set_test_progress(self, progress: ValidationProgress) -> None:
        self._progress.set_progress(progress)

    def set_export_status(self, message: str) -> None:
        self._export_status.setText(message)

    def set_theme_style(self, *, dark: bool) -> None:
        self.setStyleSheet(_DARK_STYLE if dark else _LIGHT_STYLE)


_LIGHT_STYLE = """
QFrame#micaControlPanel {
    background: rgba(255, 255, 255, 222);
    border: 1px solid rgba(0, 0, 0, 30);
    border-radius: 12px;
    color: #151515;
}
QFrame#micaControlPanel QLabel { color: #151515; }
QLabel#panelTitle { font-size: 20px; font-weight: 600; }
QLabel#progressHeading { font-weight: 600; }
QLabel#completionThanks { font-weight: 600; color: #246b2a; }
QPushButton {
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
QLabel#progressHeading { font-weight: 600; }
QLabel#completionThanks { font-weight: 600; color: #8bdc8b; }
QPushButton {
    min-height: 30px;
    padding: 0 10px;
    color: #f3f3f3;
    background: rgba(62, 62, 62, 230);
    border: 1px solid rgba(255, 255, 255, 45);
    border-radius: 5px;
}
QPushButton#exportReport { font-weight: 600; }
"""
