"""Low-frequency wallpaper metadata monitoring outside presentation paths."""

from __future__ import annotations

from PySide6.QtCore import QObject, QRunnable, QThreadPool, QTimer, Signal, Slot

from cutemica.geometry import ScreenBinding
from cutemica.providers.wallpaper_provider import WallpaperProvider
from cutemica.wallpaper import WallpaperSnapshot


class WallpaperPollSignals(QObject):
    completed = Signal(object)
    failed = Signal(str)


class WallpaperPollJob(QRunnable):
    def __init__(
        self,
        provider: WallpaperProvider,
        bindings: tuple[ScreenBinding, ...],
    ) -> None:
        super().__init__()
        self._provider = provider
        self._bindings = bindings
        self.signals = WallpaperPollSignals()

    @Slot()
    def run(self) -> None:
        try:
            snapshot = self._provider.discover(self._bindings)
        except Exception as error:  # noqa: BLE001 - cross Qt worker boundary
            self.signals.failed.emit(str(error))
            return
        self.signals.completed.emit(snapshot)


class WallpaperMonitor(QObject):
    """Publish provider snapshot changes without overlapping metadata queries."""

    snapshot_changed = Signal(object)
    failed = Signal(str)

    def __init__(
        self,
        provider: WallpaperProvider,
        bindings: tuple[ScreenBinding, ...],
        initial: WallpaperSnapshot,
        *,
        interval_ms: int = 2_000,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._provider = provider
        self._bindings = bindings
        self._current = initial
        self._active_job: WallpaperPollJob | None = None
        self._timer = QTimer(self)
        self._timer.setInterval(interval_ms)
        self._timer.timeout.connect(self.poll)

    def start(self) -> None:
        if self._provider.capabilities.wallpaper_changes:
            self._timer.start()

    def stop(self) -> None:
        self._timer.stop()

    @Slot()
    def poll(self) -> None:
        if self._active_job is not None:
            return
        if self._provider.requires_main_thread:
            self._poll_on_main_thread()
            return
        job = WallpaperPollJob(self._provider, self._bindings)
        job.signals.completed.connect(self._on_completed)
        job.signals.failed.connect(self._on_failed)
        self._active_job = job
        QThreadPool.globalInstance().start(job)

    def _poll_on_main_thread(self) -> None:
        try:
            snapshot = self._provider.discover(self._bindings)
        except Exception as error:  # noqa: BLE001 - native provider boundary
            self.failed.emit(str(error))
            return
        self._publish(snapshot)

    @Slot(object)
    def _on_completed(self, value: object) -> None:
        self._active_job = None
        if isinstance(value, WallpaperSnapshot):
            self._publish(value)

    @Slot(str)
    def _on_failed(self, message: str) -> None:
        self._active_job = None
        self.failed.emit(message)

    def _publish(self, snapshot: WallpaperSnapshot) -> None:
        if snapshot == self._current:
            return
        self._current = snapshot
        self.snapshot_changed.emit(snapshot)
