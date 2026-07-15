from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from time import perf_counter

from PIL import Image
from PySide6.QtCore import QObject, QRunnable, Signal, Slot
from PySide6.QtGui import QImage

from cutemica.core.blur_plan import resolve_blur_plan
from cutemica.core.material_field import prepare_material_field
from cutemica.core.processor import process_mica_alt
from cutemica.core.qt_image import pillow_to_qimage
from cutemica.enums import WallpaperPlacement
from cutemica.geometry import ScreenBinding
from cutemica.recipe import ResolvedMicaAltStyle


@dataclass(frozen=True, slots=True)
class MaterialRequest:
    generation: int
    cache_key: object
    wallpaper_path: Path
    placement: WallpaperPlacement
    background_color: tuple[int, int, int]
    neighbor_halo: bool
    binding: ScreenBinding
    all_bindings: tuple[ScreenBinding, ...]
    texture_scale: float
    style: ResolvedMicaAltStyle


@dataclass(frozen=True, slots=True)
class MaterialResult:
    request: MaterialRequest
    image: QImage
    elapsed_ms: float


class MaterialJobSignals(QObject):
    finished = Signal(object)
    failed = Signal(object, str)


class MaterialJob(QRunnable):
    def __init__(self, request: MaterialRequest) -> None:
        super().__init__()
        self.request = request
        self.signals = MaterialJobSignals()

    @Slot()
    def run(self) -> None:
        started = perf_counter()
        try:
            with Image.open(self.request.wallpaper_path) as wallpaper:
                texture_pixels_per_dip = self.request.binding.texture_pixels_per_dip(
                    self.request.texture_scale
                )
                blur_plan = resolve_blur_plan(
                    self.request.style,
                    texture_pixels_per_dip,
                )
                prepared = prepare_material_field(
                    wallpaper,
                    self.request.placement,
                    self.request.binding,
                    self.request.all_bindings,
                    self.request.texture_scale,
                    blur_plan,
                    self.request.background_color,
                    self.request.neighbor_halo,
                )
                processed_field = process_mica_alt(
                    prepared.image,
                    self.request.style,
                    texture_pixels_per_dip,
                )
                processed = processed_field.crop(prepared.material_box)
            elapsed_ms = (perf_counter() - started) * 1_000
            result = MaterialResult(
                request=self.request,
                image=pillow_to_qimage(processed),
                elapsed_ms=elapsed_ms,
            )
        except Exception as error:  # noqa: BLE001 - cross the Qt worker boundary safely
            self._emit_failure(str(error))
            return
        try:
            self.signals.finished.emit(result)
        except RuntimeError:
            return

    def _emit_failure(self, message: str) -> None:
        """Ignore delivery only when Qt has already destroyed the receiver source."""

        try:
            self.signals.failed.emit(self.request, message)
        except RuntimeError:
            return
