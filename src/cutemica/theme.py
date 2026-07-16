from __future__ import annotations

from typing import cast

from PySide6.QtCore import QObject, Qt, Signal, Slot
from PySide6.QtGui import QGuiApplication

from cutemica.enums import ResolvedTheme, ThemeMode
from cutemica.providers.system_theme import create_system_theme_provider
from cutemica.providers.theme_provider import ThemeProvider
from cutemica.theme_monitor import ThemeMonitor


class ThemeController(QObject):
    theme_changed = Signal(object)
    system_theme_changed = Signal(object)
    monitoring_failed = Signal(str)

    def __init__(
        self,
        mode: ThemeMode = ThemeMode.AUTO,
        parent: QObject | None = None,
        *,
        provider: ThemeProvider | None = None,
    ) -> None:
        super().__init__(parent)
        application = cast(QGuiApplication | None, QGuiApplication.instance())
        if application is None:
            raise RuntimeError("ThemeController requires a QGuiApplication")
        self._mode = mode
        self._provider = provider or create_system_theme_provider()
        self._system_theme = self._resolve_system_theme(application)
        self._resolved = self._resolve()
        application.styleHints().colorSchemeChanged.connect(
            self._on_system_theme_changed
        )
        self._monitor: ThemeMonitor | None = None
        if self._provider is not None:
            self._monitor = ThemeMonitor(
                self._provider, self._system_theme, parent=self
            )
            self._monitor.theme_changed.connect(self._on_provider_theme_changed)
            self._monitor.failed.connect(self.monitoring_failed)
            self._monitor.start()

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
        if self._provider is None:
            application = cast(QGuiApplication, QGuiApplication.instance())
            self._publish_system_theme(self._qt_theme(application))

    def _publish_system_theme(self, theme: ResolvedTheme) -> None:
        if theme is self._system_theme:
            return
        self._system_theme = theme
        self.system_theme_changed.emit(theme)
        if self._mode is ThemeMode.AUTO:
            self._publish_if_changed()

    @Slot(object)
    def _on_provider_theme_changed(self, value: object) -> None:
        if not isinstance(value, ResolvedTheme):
            return
        self._publish_system_theme(value)

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
        return self._system_theme

    def _resolve_system_theme(self, application: QGuiApplication) -> ResolvedTheme:
        if self._provider is not None:
            try:
                return self._provider.resolve()
            except RuntimeError:
                pass
        return self._qt_theme(application)

    @staticmethod
    def _qt_theme(application: QGuiApplication) -> ResolvedTheme:
        scheme = application.styleHints().colorScheme()
        return (
            ResolvedTheme.DARK if scheme is Qt.ColorScheme.Dark else ResolvedTheme.LIGHT
        )
