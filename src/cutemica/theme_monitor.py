"""Asynchronous low-frequency monitoring of desktop theme settings."""

from __future__ import annotations

from PySide6.QtCore import QObject, QRunnable, QThreadPool, QTimer, Signal, Slot

from cutemica.enums import ResolvedTheme
from cutemica.providers.theme_provider import ThemeProvider


class ThemePollSignals(QObject):
    completed = Signal(object)
    failed = Signal(str)


class ThemePollJob(QRunnable):
    def __init__(self, provider: ThemeProvider) -> None:
        super().__init__()
        self._provider = provider
        self.signals = ThemePollSignals()

    @Slot()
    def run(self) -> None:
        try:
            theme = self._provider.resolve()
        except Exception as error:  # noqa: BLE001 - cross Qt worker boundary
            self.signals.failed.emit(str(error))
            return
        self.signals.completed.emit(theme)


class ThemeMonitor(QObject):
    """Publish desktop theme changes without blocking the GUI thread."""

    theme_changed = Signal(object)
    failed = Signal(str)

    def __init__(
        self,
        provider: ThemeProvider,
        initial: ResolvedTheme,
        *,
        interval_ms: int = 1_000,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._provider = provider
        self._current = initial
        self._active_job: ThemePollJob | None = None
        self._timer = QTimer(self)
        self._timer.setInterval(interval_ms)
        self._timer.timeout.connect(self.poll)

    def start(self) -> None:
        self._timer.start()

    def stop(self) -> None:
        self._timer.stop()

    @Slot()
    def poll(self) -> None:
        if self._active_job is not None:
            return
        job = ThemePollJob(self._provider)
        job.signals.completed.connect(self._on_completed)
        job.signals.failed.connect(self._on_failed)
        self._active_job = job
        QThreadPool.globalInstance().start(job)

    @Slot(object)
    def _on_completed(self, value: object) -> None:
        self._active_job = None
        if not isinstance(value, ResolvedTheme) or value is self._current:
            return
        self._current = value
        self.theme_changed.emit(value)

    @Slot(str)
    def _on_failed(self, message: str) -> None:
        self._active_job = None
        self.failed.emit(message)
