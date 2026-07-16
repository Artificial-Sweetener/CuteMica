"""Non-visible native Qt window that records CuteMica drag presentations."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter

from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QImage, QMoveEvent, QPixmap
from PySide6.QtWidgets import QApplication, QWidget

from cutemica.controller import MaterialController
from cutemica.enums import ThemeMode, WallpaperPlacement
from cutemica.geometry import ScreenBinding, WindowGeometry
from cutemica.providers.window_geometry import WindowGeometryProvider
from cutemica.theme import ThemeController
from cutemica.wallpaper import WallpaperSnapshot, WallpaperSource
from cutemica.widgets.backdrop import PortableMicaBackdrop


@dataclass(frozen=True, slots=True)
class DragPresentationSample:
    geometry: WindowGeometry
    geometry_ms: float
    presentation_ms: float
    paint_ms: float


class NativeDragProbeWindow(QWidget):
    """Exercise the production geometry/backdrop path without visible output."""

    def __init__(
        self,
        application: QApplication,
        bindings: tuple[ScreenBinding, ...],
        geometry_provider: WindowGeometryProvider,
        materials: dict[str, QPixmap],
        size: tuple[int, int],
        clock: Callable[[], float] = perf_counter,
    ) -> None:
        flags = (
            Qt.WindowType.Tool
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowDoesNotAcceptFocus
        )
        super().__init__(None, flags)
        self._application = application
        self._clock = clock
        self._geometry_provider = geometry_provider
        self._samples: list[DragPresentationSample] = []
        self._move_cycles_ms: list[float] = []
        self._recording = False
        self._forced_presentations = 0
        self._move_events = 0
        self._generation_count = 0
        controller = MaterialController(
            WallpaperSnapshot.single(
                "native-drag-probe",
                WallpaperSource(Path(__file__), WallpaperPlacement.FILL),
            ),
            bindings,
            ThemeController(ThemeMode.DARK),
            parent=self,
        )
        controller.generation_started.connect(self._record_generation)
        self._controller = controller
        self._backdrop = PortableMicaBackdrop(controller, self, clock=clock)
        self.resize(*size)
        self._backdrop.setGeometry(self.rect())
        for screen_key, material in materials.items():
            self._backdrop.set_material(screen_key, material)
        self._material_cache_signature = self._backdrop.material_cache_signature
        self.setWindowOpacity(0.0)

    @property
    def samples(self) -> tuple[DragPresentationSample, ...]:
        return tuple(self._samples)

    @property
    def move_cycles_ms(self) -> tuple[float, ...]:
        return tuple(self._move_cycles_ms)

    @property
    def forced_presentations(self) -> int:
        return self._forced_presentations

    @property
    def move_events(self) -> int:
        return self._move_events

    @property
    def generation_count(self) -> int:
        return self._generation_count

    @property
    def registration(self) -> object:
        return self._geometry_provider.registration

    @property
    def fallback_color(self) -> tuple[int, int, int]:
        return self._controller.fallback_color

    @property
    def material_cache_stable(self) -> bool:
        return self._backdrop.material_cache_signature == self._material_cache_signature

    def isActiveWindow(self) -> bool:  # noqa: N802 - Qt test-window override
        """Keep material painting active without taking desktop focus."""

        return True

    def moveEvent(self, event: QMoveEvent) -> None:  # noqa: N802 - Qt override
        super().moveEvent(event)
        self._move_events += int(self._recording)
        self._present()

    def start(self, initial_position: QPoint) -> None:
        """Create and expose the native backing window at zero opacity."""

        self.move(initial_position)
        self.show()
        self._application.processEvents()
        self._present()
        self._application.processEvents()

    def begin_recording(self) -> None:
        self.clear_timings()
        self._generation_count = 0
        self._recording = True

    def clear_timings(self) -> None:
        """Discard warm-up or stability timings while preserving invariants."""

        self._samples.clear()
        self._move_cycles_ms.clear()
        self._forced_presentations = 0
        self._move_events = 0

    def step(self, position: QPoint) -> DragPresentationSample:
        """Move through the native event loop and guarantee one presentation."""

        previous_count = len(self._samples)
        started = self._clock()
        self.move(position)
        self._application.processEvents()
        if len(self._samples) == previous_count:
            self._forced_presentations += 1
            self._present()
            self._application.processEvents()
        self._move_cycles_ms.append((self._clock() - started) * 1_000)
        if len(self._samples) == previous_count:
            raise RuntimeError("Native drag did not produce a presentation")
        return self._samples[-1]

    def capture(self) -> QImage:
        """Capture only CuteMica's widget backing store, never the desktop."""

        return self._backdrop.grab().toImage()

    def finish(self) -> None:
        self._recording = False
        self.close()
        self._application.processEvents()

    def _present(self) -> None:
        geometry_started = self._clock()
        geometry = self._geometry_provider.snapshot(self)
        geometry_ms = (self._clock() - geometry_started) * 1_000
        presentation_started = self._clock()
        self._backdrop.present(geometry, immediate=True)
        presentation_ms = (self._clock() - presentation_started) * 1_000
        if self._recording:
            self._samples.append(
                DragPresentationSample(
                    geometry,
                    geometry_ms,
                    presentation_ms,
                    self._backdrop.paint_metrics.latest_ms,
                )
            )

    def _record_generation(self, _generation: int) -> None:
        if self._recording:
            self._generation_count += 1
