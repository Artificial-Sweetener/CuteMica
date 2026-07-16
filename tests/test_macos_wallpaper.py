from pathlib import Path

from PIL import Image

from cutemica.enums import WallpaperPlacement
from cutemica.geometry import Rect, ScreenBinding
from cutemica.providers.macos_appkit import MacDesktopRecord
from cutemica.providers.macos_wallpaper import MacOSWallpaperProvider


def test_macos_matches_cocoa_screens_to_qt_coordinates(tmp_path: Path) -> None:
    main_path = tmp_path / "main.png"
    upper_path = tmp_path / "upper.png"
    Image.new("RGB", (8, 8)).save(main_path)
    Image.new("RGB", (8, 8)).save(upper_path)
    records = (
        MacDesktopRecord(
            main_path,
            (0.0, 0.0, 1920.0, 1080.0),
            WallpaperPlacement.FILL,
            (1, 2, 3),
        ),
        MacDesktopRecord(
            upper_path,
            (0.0, 1080.0, 1280.0, 720.0),
            WallpaperPlacement.FIT,
            (4, 5, 6),
        ),
    )
    main_geometry = Rect(0, 0, 1920, 1080)
    upper_geometry = Rect(0, -720, 1280, 720)
    bindings = (
        ScreenBinding("main", main_geometry, "main", main_geometry, 1.0),
        ScreenBinding("upper", upper_geometry, "upper", upper_geometry, 1.0),
    )

    snapshot = MacOSWallpaperProvider(lambda: records).discover(bindings)

    assert snapshot.source_for(bindings[0]).path == main_path
    assert snapshot.source_for(bindings[1]).path == upper_path
    assert snapshot.source_for(bindings[1]).background_color == (4, 5, 6)


def test_macos_provider_reads_fresh_records_for_image_changes(tmp_path: Path) -> None:
    first_path = tmp_path / "first.png"
    second_path = tmp_path / "second.png"
    Image.new("RGB", (8, 8)).save(first_path)
    Image.new("RGB", (8, 8)).save(second_path)
    frame = (0.0, 0.0, 1920.0, 1080.0)
    geometry = Rect(0, 0, 1920, 1080)
    binding = ScreenBinding("main", geometry, "main", geometry, 1.0)
    paths = iter((first_path, second_path))

    def read() -> tuple[MacDesktopRecord, ...]:
        return (
            MacDesktopRecord(
                next(paths),
                frame,
                WallpaperPlacement.FILL,
                (0, 0, 0),
            ),
        )

    provider = MacOSWallpaperProvider(read)

    assert provider.discover((binding,)).default_source.path == first_path
    assert provider.discover((binding,)).default_source.path == second_path
