import json
from pathlib import Path

import pytest
from PIL import Image

from cutemica.enums import WallpaperPlacement
from cutemica.geometry import Rect, ScreenBinding
from cutemica.providers.plasma_wallpaper import PlasmaWallpaperProvider


def _binding(identifier: str, x: int) -> ScreenBinding:
    geometry = Rect(x, 0, 100, 100)
    return ScreenBinding(identifier, geometry, identifier, geometry, 1.0)


def test_plasma_publishes_per_screen_sources(tmp_path: Path) -> None:
    left = tmp_path / "left.png"
    right = tmp_path / "right.png"
    Image.new("RGB", (8, 8)).save(left)
    Image.new("RGB", (8, 8)).save(right)
    records = [
        {
            "screen": 0,
            "plugin": "org.kde.image",
            "image": left.as_uri(),
            "fillMode": 2,
            "color": "#102030",
        },
        {
            "screen": 1,
            "plugin": "org.kde.image",
            "image": right.as_uri(),
            "fillMode": 1,
            "color": "#405060",
        },
    ]
    bindings = (_binding("left", 0), _binding("right", 100))
    provider = PlasmaWallpaperProvider(lambda _arguments: json.dumps(records))

    snapshot = provider.discover(bindings)

    assert snapshot.source_for(bindings[0]).path == left
    assert snapshot.source_for(bindings[0]).placement is WallpaperPlacement.FILL
    assert snapshot.source_for(bindings[1]).path == right
    assert snapshot.source_for(bindings[1]).placement is WallpaperPlacement.FIT


def test_plasma_rejects_live_wallpaper_plugins(tmp_path: Path) -> None:
    records = [
        {
            "screen": 0,
            "plugin": "org.kde.slideshow",
            "image": str(tmp_path),
            "fillMode": 2,
            "color": "#000000",
        }
    ]
    provider = PlasmaWallpaperProvider(lambda _arguments: json.dumps(records))

    with pytest.raises(RuntimeError, match="not a static image"):
        provider.discover((_binding("screen", 0),))
