from PySide6.QtGui import QPixmap
from pytestqt.qtbot import QtBot

from cutemica.cache import MaterialCache, MaterialCacheKey
from cutemica.enums import ResolvedTheme, WallpaperPlacement
from cutemica.geometry import Rect, ScreenBinding


def cache_key(theme: ResolvedTheme) -> MaterialCacheKey:
    geometry = Rect(0, 0, 100, 100)
    binding = ScreenBinding("screen", geometry, "screen", geometry, 1.0)
    return MaterialCacheKey(
        "wallpaper",
        WallpaperPlacement.FILL,
        (0, 0, 0),
        binding,
        (binding,),
        theme,
        "v0",
    )


def test_cache_returns_an_independent_qpixmap_handle(qtbot: QtBot) -> None:
    del qtbot
    cache = MaterialCache()
    key = cache_key(ResolvedTheme.DARK)
    material = QPixmap(4, 4)
    cache.put(key, material)

    cached = cache.get(key)

    assert cached is not None
    assert cached.size() == material.size()
    assert cached.cacheKey() == material.cacheKey()
    assert len(cache) == 1


def test_cache_clear_removes_materials(qtbot: QtBot) -> None:
    del qtbot
    cache = MaterialCache()
    key = cache_key(ResolvedTheme.LIGHT)
    cache.put(key, QPixmap(1, 1))

    cache.clear()

    assert cache.get(key) is None


def test_cache_evicts_the_least_recent_material_at_its_capacity(
    qtbot: QtBot,
) -> None:
    del qtbot
    cache = MaterialCache(capacity=1)
    old_key = cache_key(ResolvedTheme.LIGHT)
    current_key = cache_key(ResolvedTheme.DARK)
    cache.put(old_key, QPixmap(1, 1))

    cache.put(current_key, QPixmap(1, 1))

    assert cache.get(old_key) is None
    assert cache.get(current_key) is not None
    assert len(cache) == 1
