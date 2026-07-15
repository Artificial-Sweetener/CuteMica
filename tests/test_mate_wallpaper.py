from pathlib import Path

from PIL import Image

from cutemica.enums import WallpaperPlacement
from cutemica.providers.mate_wallpaper import MateWallpaperProvider


def test_mate_discovers_wallpaper_placement_and_color(tmp_path: Path) -> None:
    wallpaper = tmp_path / "mate wallpaper.png"
    Image.new("RGB", (8, 8)).save(wallpaper)
    values = {
        "picture-filename": f"'{wallpaper}'",
        "picture-options": "'centered'",
        "primary-color": "'#abc'",
    }

    def run(arguments: tuple[str, ...]) -> str:
        assert arguments[2] == "org.mate.background"
        return values[arguments[3]]

    snapshot = MateWallpaperProvider(run).discover(())

    assert snapshot.provider_name == "mate"
    assert snapshot.default_source.path == wallpaper
    assert snapshot.default_source.placement is WallpaperPlacement.CENTER
    assert snapshot.default_source.background_color == (0xAA, 0xBB, 0xCC)
