from __future__ import annotations

from PySide6.QtCore import QObject, QThreadPool, Signal, Slot
from PySide6.QtGui import QPixmap

from cutemica.cache import MaterialCache, MaterialCacheKey
from cutemica.enums import ResolvedTheme
from cutemica.geometry import ScreenBinding
from cutemica.recipe import MicaAltRecipe
from cutemica.scheduler import MaterialJob, MaterialRequest, MaterialResult
from cutemica.theme import ThemeController
from cutemica.wallpaper import WallpaperSnapshot, WallpaperSource


class MaterialController(QObject):
    material_ready = Signal(str, QPixmap, float)
    generation_started = Signal(int)
    generation_finished = Signal(int)
    error = Signal(str)
    wallpaper_changed = Signal(object)

    def __init__(
        self,
        wallpaper: WallpaperSnapshot,
        bindings: tuple[ScreenBinding, ...],
        theme: ThemeController,
        recipe: MicaAltRecipe | None = None,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        wallpaper.validate()
        if not bindings:
            raise ValueError("At least one screen binding is required")
        self._wallpaper = wallpaper
        self._wallpaper_state = wallpaper.state_signature
        self._bindings = bindings
        self._theme = theme
        self._recipe = recipe or MicaAltRecipe()
        self._cache = MaterialCache(capacity=len(bindings))
        self._pool = QThreadPool.globalInstance()
        self._generation = 0
        self._pending = 0
        self._jobs: dict[tuple[int, str], MaterialJob] = {}
        theme.theme_changed.connect(self.refresh)

    @property
    def bindings(self) -> tuple[ScreenBinding, ...]:
        return self._bindings

    @property
    def resolved_theme(self) -> ResolvedTheme:
        return self._theme.resolved

    @property
    def fallback_color(self) -> tuple[int, int, int]:
        return self._recipe.resolve(self._theme.resolved).fallback_color

    @property
    def wallpaper(self) -> WallpaperSnapshot:
        return self._wallpaper

    def set_wallpaper(self, wallpaper: WallpaperSnapshot) -> None:
        """Publish a new provider snapshot and regenerate affected materials."""

        wallpaper.validate()
        state = wallpaper.state_signature
        if state == self._wallpaper_state:
            return
        self._wallpaper = wallpaper
        self._wallpaper_state = state
        self._cache.clear()
        self.wallpaper_changed.emit(wallpaper)
        self.refresh()

    def binding_for_screen(self, screen_name: str) -> ScreenBinding:
        return next(
            (
                binding
                for binding in self._bindings
                if binding.qt_screen_name == screen_name
            ),
            self._bindings[0],
        )

    @Slot()
    def refresh(self) -> None:
        self._generation += 1
        generation = self._generation
        self._pending = len(self._bindings)
        self.generation_started.emit(generation)
        for binding in self._bindings:
            source = self._wallpaper.source_for(binding)
            cache_key = self._cache_key(binding)
            cached = self._cache.get(cache_key)
            if cached is not None:
                self.material_ready.emit(binding.cache_key, cached, 0.0)
                self._complete_one(generation)
                continue
            texture_scale = self._recipe.texture_scale_for(binding.device_pixel_ratio)
            request = MaterialRequest(
                generation=generation,
                cache_key=cache_key,
                wallpaper_path=source.path,
                placement=source.placement,
                background_color=source.background_color,
                neighbor_halo=self._uses_shared_source(source),
                binding=binding,
                all_bindings=self._bindings,
                texture_scale=texture_scale,
                style=self._recipe.resolve(
                    self._theme.resolved,
                    binding.device_pixel_ratio,
                ),
            )
            job = MaterialJob(request)
            job.signals.finished.connect(self._on_job_finished)
            job.signals.failed.connect(self._on_job_failed)
            self._jobs[(generation, binding.cache_key)] = job
            self._pool.start(job)

    @Slot(object)
    def _on_job_finished(self, result_object: object) -> None:
        if not isinstance(result_object, MaterialResult):
            return
        result = result_object
        request = result.request
        self._jobs.pop((request.generation, request.binding.cache_key), None)
        if request.generation != self._generation:
            return
        if not isinstance(request.cache_key, MaterialCacheKey):
            self.error.emit("Worker returned an invalid cache key")
            self._complete_one(request.generation)
            return
        material = QPixmap.fromImage(result.image)
        self._cache.put(request.cache_key, material)
        self.material_ready.emit(
            request.binding.cache_key,
            material,
            result.elapsed_ms,
        )
        self._complete_one(request.generation)

    @Slot(object, str)
    def _on_job_failed(self, request_object: object, message: str) -> None:
        if not isinstance(request_object, MaterialRequest):
            return
        request = request_object
        self._jobs.pop((request.generation, request.binding.cache_key), None)
        if request.generation != self._generation:
            return
        self.error.emit(message)
        self._complete_one(request.generation)

    def _cache_key(self, binding: ScreenBinding) -> MaterialCacheKey:
        source = self._wallpaper.source_for(binding)
        return MaterialCacheKey(
            wallpaper_signature=source.signature,
            placement=source.placement,
            background_color=source.background_color,
            binding=binding,
            topology=self._bindings,
            theme=self._theme.resolved,
            recipe_version=self._recipe.version,
        )

    def _complete_one(self, generation: int) -> None:
        if generation != self._generation:
            return
        self._pending -= 1
        if self._pending == 0:
            self.generation_finished.emit(generation)

    def _uses_shared_source(self, source: WallpaperSource) -> bool:
        return all(
            self._wallpaper.source_for(binding) == source for binding in self._bindings
        )
