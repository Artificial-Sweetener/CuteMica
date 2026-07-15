from __future__ import annotations

from typing import cast

from PySide6.QtCore import QObject, Qt, Signal
from PySide6.QtGui import QGuiApplication

from cutemica.enums import ResolvedTheme, ThemeMode


class ThemeController(QObject):
    theme_changed = Signal(object)

    def __init__(
        self, mode: ThemeMode = ThemeMode.AUTO, parent: QObject | None = None
    ) -> None:
        super().__init__(parent)
        self._mode = mode
        self._resolved = self._resolve()
        application = cast(QGuiApplication | None, QGuiApplication.instance())
        if application is None:
            raise RuntimeError("ThemeController requires a QGuiApplication")
        application.styleHints().colorSchemeChanged.connect(
            self._on_system_theme_changed
        )

    @property
    def mode(self) -> ThemeMode:
        return self._mode

    @property
    def resolved(self) -> ResolvedTheme:
        return self._resolved

    def set_mode(self, mode: ThemeMode) -> None:
        if mode is self._mode:
            return
        self._mode = mode
        self._publish_if_changed()

    def _on_system_theme_changed(self, _scheme: Qt.ColorScheme) -> None:
        if self._mode is ThemeMode.AUTO:
            self._publish_if_changed()

    def _publish_if_changed(self) -> None:
        resolved = self._resolve()
        if resolved is self._resolved:
            return
        self._resolved = resolved
        self.theme_changed.emit(resolved)

    def _resolve(self) -> ResolvedTheme:
        if self._mode is ThemeMode.LIGHT:
            return ResolvedTheme.LIGHT
        if self._mode is ThemeMode.DARK:
            return ResolvedTheme.DARK
        application = cast(QGuiApplication | None, QGuiApplication.instance())
        if application is None:
            return ResolvedTheme.LIGHT
        scheme = application.styleHints().colorScheme()
        return (
            ResolvedTheme.DARK if scheme is Qt.ColorScheme.Dark else ResolvedTheme.LIGHT
        )
