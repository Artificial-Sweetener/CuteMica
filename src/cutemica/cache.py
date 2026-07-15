from collections import OrderedDict
from dataclasses import dataclass

from PySide6.QtGui import QPixmap

from cutemica.enums import ResolvedTheme, WallpaperPlacement
from cutemica.geometry import ScreenBinding


@dataclass(frozen=True, slots=True)
class MaterialCacheKey:
    wallpaper_signature: str
    placement: WallpaperPlacement
    background_color: tuple[int, int, int]
    binding: ScreenBinding
    topology: tuple[ScreenBinding, ...]
    theme: ResolvedTheme
    recipe_version: str


class MaterialCache:
    def __init__(self, capacity: int = 1) -> None:
        if capacity < 1:
            raise ValueError("Material cache capacity must be positive")
        self._capacity = capacity
        self._materials: OrderedDict[MaterialCacheKey, QPixmap] = OrderedDict()

    def get(self, key: MaterialCacheKey) -> QPixmap | None:
        material = self._materials.get(key)
        if material is not None:
            self._materials.move_to_end(key)
        return QPixmap(material) if material is not None else None

    def put(self, key: MaterialCacheKey, material: QPixmap) -> None:
        self._materials[key] = QPixmap(material)
        self._materials.move_to_end(key)
        while len(self._materials) > self._capacity:
            self._materials.popitem(last=False)

    def clear(self) -> None:
        self._materials.clear()

    def __len__(self) -> int:
        return len(self._materials)
