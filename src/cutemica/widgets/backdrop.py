from __future__ import annotations

from time import perf_counter

from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QPainter, QPaintEvent, QPixmap
from PySide6.QtWidgets import QWidget

from cutemica.controller import MaterialController
from cutemica.geometry import WindowGeometry
from cutemica.metrics import PaintMetrics
from cutemica.viewport import MaterialSlice, plan_material_slices
from cutemica.widgets.material_painter import paint_material_slices


class PortableMicaBackdrop(QWidget):
    """Opaque, low-cost presenter for precomputed per-screen material textures."""

    def __init__(self, controller: MaterialController, parent: QWidget) -> None:
        super().__init__(parent)
        self._controller = controller
        self._materials: dict[str, QPixmap] = {}
        self._material_sizes: dict[str, tuple[int, int]] = {}
        self._window_geometry: WindowGeometry | None = None
        self._metrics = PaintMetrics()
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
        self.setAutoFillBackground(False)
        controller.material_ready.connect(self._on_material_ready)

    @property
    def paint_metrics(self) -> PaintMetrics:
        return self._metrics

    @property
    def material_cache_signature(self) -> tuple[tuple[str, int], ...]:
        """Identify published textures without copying their pixel storage."""

        return tuple(
            sorted(
                (key, material.cacheKey()) for key, material in self._materials.items()
            )
        )

    def set_material(self, screen_key: str, material: QPixmap) -> None:
        """Publish a prepared screen material to the low-cost presenter."""

        self._materials[screen_key] = QPixmap(material)
        self._material_sizes[screen_key] = (material.width(), material.height())
        self.update()

    def present(
        self,
        window_geometry: WindowGeometry,
        *,
        immediate: bool,
    ) -> None:
        """Publish native/local geometry and schedule its presentation."""

        self._window_geometry = window_geometry
        if immediate:
            self.repaint()
        else:
            self.update()

    @Slot(str, QPixmap, float)
    def _on_material_ready(
        self, screen_key: str, material: QPixmap, _elapsed_ms: float
    ) -> None:
        self.set_material(screen_key, material)

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: N802 - Qt override
        started = perf_counter()
        painter = QPainter(self)
        slices: tuple[MaterialSlice, ...] = ()
        representative = next(iter(self._materials.values()), None)
        if (
            material_presentation_enabled(
                self.window().isActiveWindow(), representative
            )
            and self._window_geometry is not None
        ):
            slices = plan_material_slices(
                self._window_geometry,
                self._controller.bindings,
                self._material_sizes,
            )
        paint_material_slices(
            painter,
            event.rect(),
            self._controller.fallback_color,
            slices,
            self._materials,
            paint_bounds=self.rect(),
        )
        painter.end()
        self._metrics.record((perf_counter() - started) * 1_000)


def material_presentation_enabled(
    window_active: bool,
    material: QPixmap | None,
) -> bool:
    """Return whether active-state wallpaper material should be presented."""

    return window_active and material is not None
