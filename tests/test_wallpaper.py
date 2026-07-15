from pathlib import Path

import pytest
from PIL import Image

from cutemica.enums import WallpaperPlacement
from cutemica.wallpaper import wallpaper_from_path


def test_explicit_wallpaper_is_available_to_every_platform(tmp_path: Path) -> None:
    path = tmp_path / "wallpaper.png"
    Image.new("RGB", (16, 9), (20, 40, 80)).save(path)

    source = wallpaper_from_path(path, WallpaperPlacement.FILL)

    assert source.default_source.path == path
    assert source.default_source.placement is WallpaperPlacement.FILL


def test_explicit_wallpaper_fails_fast_when_missing(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="Wallpaper does not exist"):
        wallpaper_from_path(tmp_path / "missing.png")
