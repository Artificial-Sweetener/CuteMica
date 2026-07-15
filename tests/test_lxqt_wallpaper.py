from pathlib import Path

import pytest
from PIL import Image

from cutemica.enums import WallpaperPlacement
from cutemica.geometry import Rect, ScreenBinding
from cutemica.providers.lxqt_wallpaper import LxqtWallpaperProvider


def _binding(identifier: str, x: int) -> ScreenBinding:
    geometry = Rect(x, 0, 100, 100)
    return ScreenBinding(identifier, geometry, identifier, geometry, 1.0)


def test_lxqt_reads_pcmanfm_profile(tmp_path: Path) -> None:
    wallpaper = tmp_path / "lxqt wallpaper.png"
    Image.new("RGB", (8, 8)).save(wallpaper)
    profile = tmp_path / "settings.conf"
    profile.write_text(
        "\n".join(
            (
                "[Desktop]",
                "WallpaperMode=fit",
                f"Wallpaper={wallpaper}",
                "BgColor=#123abc",
                "PerScreenWallpaper=true",
            )
        ),
        encoding="utf-8",
    )

    snapshot = LxqtWallpaperProvider(profile).discover((_binding("screen", 0),))

    assert snapshot.default_source.path == wallpaper
    assert snapshot.default_source.placement is WallpaperPlacement.FIT
    assert snapshot.default_source.background_color == (0x12, 0x3A, 0xBC)


def test_lxqt_maps_shared_zoom_to_span(tmp_path: Path) -> None:
    wallpaper = tmp_path / "spanned.png"
    Image.new("RGB", (8, 8)).save(wallpaper)
    profile = tmp_path / "settings.conf"
    profile.write_text(
        f"[Desktop]\nWallpaperMode=zoom\nWallpaper={wallpaper}\n",
        encoding="utf-8",
    )

    snapshot = LxqtWallpaperProvider(profile).discover(
        (_binding("left", 0), _binding("right", 100))
    )

    assert snapshot.default_source.placement is WallpaperPlacement.SPAN


def test_lxqt_rejects_color_only_mode(tmp_path: Path) -> None:
    profile = tmp_path / "settings.conf"
    profile.write_text("[Desktop]\nWallpaperMode=none\n", encoding="utf-8")

    with pytest.raises(RuntimeError, match="without an image"):
        LxqtWallpaperProvider(profile).discover(())
