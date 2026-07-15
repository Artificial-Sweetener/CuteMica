"""Portable demo smoke lifecycle and optional Qt screenshot capture."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, QTimer
from PySide6.QtWidgets import QApplication

from cutemica.controller import MaterialController
from cutemica.demo.window import DemoWindow
from cutemica.enums import ResolvedTheme, ThemeMode
from cutemica.theme import ThemeController


class DemoSmokeSequence(QObject):
    """Exercise material generation and theme invalidation before exiting."""

    def __init__(
        self,
        application: QApplication,
        window: DemoWindow,
        theme: ThemeController,
        controller: MaterialController,
        *,
        screenshot_path: Path | None,
        exercise_theme_change: bool,
    ) -> None:
        super().__init__(application)
        self._application = application
        self._window = window
        self._theme = theme
        self._screenshot_path = screenshot_path
        self._exercise_theme_change = exercise_theme_change
        self._generation_count = 0
        self._armed = False
        self.error: str | None = None
        controller.generation_finished.connect(self._on_generation_finished)

    def start(self) -> None:
        self._armed = True

    def _on_generation_finished(self, _generation: int) -> None:
        if not self._armed:
            return
        self._generation_count += 1
        if self._exercise_theme_change and self._generation_count == 1:
            opposite = (
                ThemeMode.LIGHT
                if self._theme.resolved is ResolvedTheme.DARK
                else ThemeMode.DARK
            )
            self._theme.set_mode(opposite)
            return
        QTimer.singleShot(100, self._finish)

    def _finish(self) -> None:
        try:
            self._save_screenshot()
        except (OSError, RuntimeError) as error:
            self.error = str(error)
            self._application.exit(1)
            return
        self._application.quit()

    def _save_screenshot(self) -> None:
        if self._screenshot_path is None:
            return
        self._screenshot_path.parent.mkdir(parents=True, exist_ok=True)
        if not self._window.grab().save(str(self._screenshot_path)):
            raise RuntimeError(f"Could not save screenshot: {self._screenshot_path}")
