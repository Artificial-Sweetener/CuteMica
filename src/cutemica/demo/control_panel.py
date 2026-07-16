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

    def __init__(
        self, wallpaper_description: str, parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self.setObjectName("micaControlPanel")
        self.setFixedWidth(430)

        title = QLabel("CuteMica")
        title.setObjectName("panelTitle")
        subtitle = QLabel(
            "Move the window across the desktop to inspect wallpaper anchoring. "
            "Theme changes regenerate the cached material off the GUI thread."
        )
        subtitle.setWordWrap(True)

        self._theme = QComboBox()
        self._theme.addItem("Follow system", ThemeMode.AUTO)
        self._theme.addItem("Light", ThemeMode.LIGHT)
        self._theme.addItem("Dark", ThemeMode.DARK)

        refresh = QPushButton("Regenerate material")
        self._status = QLabel("Waiting for first material generation")
        self._status.setWordWrap(True)
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
        layout.addSpacing(6)
        layout.addLayout(choices)
        layout.addWidget(refresh)
        layout.addSpacing(4)
        layout.addWidget(self._status)
        layout.addWidget(self._environment)

        self._theme.currentIndexChanged.connect(self._publish_theme)
        refresh.clicked.connect(self.refresh_requested)

    def set_generation_status(self, message: str) -> None:
        self._status.setText(message)

    def set_environment_description(self, description: str) -> None:
        self._environment.setText(description)

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
QComboBox, QPushButton {
    min-height: 30px;
    padding: 0 10px;
    background: rgba(255, 255, 255, 210);
    border: 1px solid rgba(0, 0, 0, 45);
    border-radius: 5px;
}
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
QComboBox, QPushButton {
    min-height: 30px;
    padding: 0 10px;
    color: #f3f3f3;
    background: rgba(62, 62, 62, 230);
    border: 1px solid rgba(255, 255, 255, 45);
    border-radius: 5px;
}
QComboBox QAbstractItemView { color: #f3f3f3; background: #303030; }
"""
