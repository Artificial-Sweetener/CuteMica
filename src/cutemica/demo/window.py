from __future__ import annotations

from time import perf_counter

from PySide6.QtCore import QEvent, QTimer, QUrl, Slot
from PySide6.QtGui import (
    QDesktopServices,
    QMoveEvent,
    QPixmap,
    QResizeEvent,
    QScreen,
    QShowEvent,
)
from PySide6.QtWidgets import QWidget

from cutemica.controller import MaterialController
from cutemica.demo.control_panel import ControlPanel
from cutemica.diagnostics.exporter import TesterReportExporter
from cutemica.diagnostics.session import ValidationSession
from cutemica.enums import ResolvedTheme
from cutemica.providers.window_geometry import WindowGeometryProvider
from cutemica.theme import ThemeController
from cutemica.wallpaper import WallpaperSnapshot
from cutemica.widgets import PortableMicaBackdrop


class DemoWindow(QWidget):
    """Portable CuteMica demonstration window with a standard Qt frame."""

    def __init__(
        self,
        controller: MaterialController,
        theme: ThemeController,
        wallpaper: WallpaperSnapshot,
        window_geometry: WindowGeometryProvider,
        session: ValidationSession,
    ) -> None:
        super().__init__()
        self._controller = controller
        self._window_geometry = window_geometry
        self._session = session
        self._wallpaper = wallpaper
        self._report_exporter = TesterReportExporter(
            controller.bindings,
            window_geometry.registration.value,
        )
        self._latest_generation_ms = 0.0
        self._screen_signal_connected = False
        self._screenshot_active = False
        self.setWindowTitle("CuteMica")
        self.resize(1040, 760)
        self.setMinimumSize(760, 640)

        self._backdrop = PortableMicaBackdrop(controller, self)
        self._panel = ControlPanel(
            _environment_description(wallpaper, window_geometry.registration.value),
            self,
        )
        self._panel.reset_session_requested.connect(self._reset_session)
        self._panel.export_report_requested.connect(self._export_report)
        controller.generation_started.connect(self._on_generation_started)
        controller.material_ready.connect(self._on_material_ready)
        controller.generation_finished.connect(self._on_generation_finished)
        controller.error.connect(self._on_controller_error)
        controller.wallpaper_changed.connect(self._on_wallpaper_changed)
        theme.theme_changed.connect(self._on_theme_changed)
        theme.system_theme_changed.connect(self._on_system_theme_changed)
        theme.monitoring_failed.connect(self._on_theme_monitor_failed)
        self._status_timer = QTimer(self)
        self._status_timer.setInterval(250)
        self._status_timer.timeout.connect(self._update_test_status)
        self._status_timer.start()
        self._layout_children()
        self._on_theme_changed(theme.resolved)

    @property
    def paint_metrics(self) -> tuple[float, float]:
        metrics = self._backdrop.paint_metrics
        return metrics.average_ms, metrics.maximum_ms

    def isActiveWindow(self) -> bool:  # noqa: N802 - Qt override
        """Treat an explicit screenshot as active in windowless CI sessions."""

        return self._screenshot_active or super().isActiveWindow()

    def prepare_screenshot(self) -> None:
        """Present the material synchronously before capturing this widget."""

        self._screenshot_active = True
        self._present_backdrop(immediate=True)

    def showEvent(self, event: QShowEvent) -> None:  # noqa: N802 - Qt override
        super().showEvent(event)
        window_handle = self.windowHandle()
        if window_handle is not None and not self._screen_signal_connected:
            window_handle.screenChanged.connect(self._on_window_screen_changed)
            self._screen_signal_connected = True
        QTimer.singleShot(0, self._start_after_show)

    def resizeEvent(self, event: QResizeEvent) -> None:  # noqa: N802 - Qt override
        super().resizeEvent(event)
        self._layout_children()
        self._present_backdrop(immediate=True)

    def moveEvent(self, event: QMoveEvent) -> None:  # noqa: N802 - Qt override
        super().moveEvent(event)
        started = perf_counter()
        geometry_started = perf_counter()
        geometry = self._window_geometry.snapshot(self)
        geometry_ms = (perf_counter() - geometry_started) * 1_000
        presentation_started = perf_counter()
        self._backdrop.present(geometry, immediate=True)
        presentation_ms = (perf_counter() - presentation_started) * 1_000
        self._session.record_motion(
            geometry,
            move_cycle_ms=(perf_counter() - started) * 1_000,
            geometry_ms=geometry_ms,
            presentation_ms=presentation_ms,
            paint_ms=self._backdrop.paint_metrics.latest_ms,
        )

    def changeEvent(self, event: QEvent) -> None:  # noqa: N802 - Qt override
        super().changeEvent(event)
        if event.type() == QEvent.Type.ActivationChange and hasattr(self, "_backdrop"):
            self._present_backdrop(immediate=False)

    def _start_after_show(self) -> None:
        self._present_backdrop(immediate=False)
        self._controller.refresh()

    def _present_backdrop(self, *, immediate: bool) -> None:
        if not hasattr(self, "_backdrop"):
            return
        self._backdrop.present(
            self._window_geometry.snapshot(self),
            immediate=immediate,
        )

    @Slot(QScreen)
    def _on_window_screen_changed(self, _screen: QScreen) -> None:
        self._present_backdrop(immediate=True)

    def _layout_children(self) -> None:
        if not hasattr(self, "_backdrop") or not hasattr(self, "_panel"):
            return
        self._backdrop.setGeometry(self.rect())
        self._panel.adjustSize()
        panel_x = max(26, (self.width() - self._panel.width()) // 2)
        panel_y = max(26, (self.height() - self._panel.height()) // 2)
        self._panel.move(panel_x, panel_y)
        self._backdrop.lower()
        self._panel.raise_()

    @Slot(object)
    def _on_theme_changed(self, theme_object: object) -> None:
        if isinstance(theme_object, ResolvedTheme):
            self._panel.set_theme_style(dark=theme_object is ResolvedTheme.DARK)

    @Slot(object)
    def _on_system_theme_changed(self, theme_object: object) -> None:
        if isinstance(theme_object, ResolvedTheme):
            self._session.record_theme(theme_object)

    @Slot(object)
    def _on_wallpaper_changed(self, value: object) -> None:
        if isinstance(value, WallpaperSnapshot):
            self._wallpaper = value
            self._session.record_wallpaper_change(value.provider_name)
            self._panel.set_environment_description(
                _environment_description(
                    value,
                    self._window_geometry.registration.value,
                )
            )

    @Slot(int)
    def _on_generation_started(self, generation: int) -> None:
        self._latest_generation_ms = 0.0
        self._panel.set_generation_status(f"Generating material set {generation}…")

    @Slot(str, QPixmap, float)
    def _on_material_ready(
        self, _screen_key: str, _material: QPixmap, elapsed_ms: float
    ) -> None:
        self._latest_generation_ms = max(self._latest_generation_ms, elapsed_ms)

    @Slot(int)
    def _on_generation_finished(self, generation: int) -> None:
        average_ms, maximum_ms = self.paint_metrics
        self._panel.set_generation_status(
            f"Material set {generation} ready in {self._latest_generation_ms:.1f} ms · "
            f"paint avg {average_ms:.3f} ms / max {maximum_ms:.3f} ms"
        )
        self._session.record_generation(generation, self._latest_generation_ms)

    @Slot(str)
    def _on_theme_monitor_failed(self, message: str) -> None:
        self._session.record_error("theme-monitor", message)

    @Slot(str)
    def _on_controller_error(self, message: str) -> None:
        self._session.record_error("material-or-wallpaper", message)
        self._panel.set_generation_status(message)

    @Slot()
    def _reset_session(self) -> None:
        self._session.reset()
        self._panel.set_export_status("")
        self._update_test_status()

    @Slot()
    def _update_test_status(self) -> None:
        self._panel.set_test_progress(self._session.progress)

    @Slot()
    def _export_report(self) -> None:
        try:
            output = self._report_exporter.export(self._session, self._wallpaper)
        except OSError as error:
            self._session.record_error("report-export", str(error))
            self._panel.set_export_status(f"Could not save report: {error}")
            return
        self._panel.set_export_status(f"Saved {output.name}")
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(output.parent)))


def _environment_description(wallpaper: WallpaperSnapshot, registration: str) -> str:
    return (
        f"Wallpaper: {wallpaper.display_name}\n"
        f"Provider: {wallpaper.provider_name}\n"
        f"Registration: {registration}"
    )
