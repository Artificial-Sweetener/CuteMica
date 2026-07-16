from pathlib import Path

from PIL import Image

from cutemica.enums import WallpaperPlacement
from cutemica.geometry import Rect, ScreenBinding
from cutemica.providers.windows_desktop_api import WindowsDesktopRecord
from cutemica.providers.windows_wallpaper import WindowsWallpaperProvider


def test_windows_matches_desktop_records_to_native_monitor_geometry(
    tmp_path: Path,
) -> None:
    left_path = tmp_path / "left.png"
    main_path = tmp_path / "main.png"
    Image.new("RGB", (8, 8)).save(left_path)
    Image.new("RGB", (8, 8)).save(main_path)
    left_geometry = Rect(-1280, 0, 1280, 720)
    main_geometry = Rect(0, 0, 1920, 1080)
    records = (
        WindowsDesktopRecord(
            "main-native",
            main_path,
            main_geometry,
            WallpaperPlacement.FILL,
            (1, 2, 3),
        ),
        WindowsDesktopRecord(
            "left-native",
            left_path,
            left_geometry,
            WallpaperPlacement.FILL,
            (1, 2, 3),
        ),
    )
    bindings = (
        ScreenBinding("left", left_geometry, "left", left_geometry, 1.0),
        ScreenBinding("main", main_geometry, "main", main_geometry, 1.0),
    )

    snapshot = WindowsWallpaperProvider(lambda: records).discover(bindings)

    assert snapshot.source_for(bindings[0]).path == left_path
    assert snapshot.source_for(bindings[1]).path == main_path
    assert len(snapshot.per_screen) == len(bindings)


def test_windows_provider_reads_fresh_records_for_slideshow_changes(
    tmp_path: Path,
) -> None:
    first_path = tmp_path / "first.png"
    second_path = tmp_path / "second.png"
    Image.new("RGB", (8, 8)).save(first_path)
    Image.new("RGB", (8, 8)).save(second_path)
    geometry = Rect(0, 0, 1920, 1080)
    binding = ScreenBinding("main", geometry, "main", geometry, 1.0)
    paths = iter((first_path, second_path))

    def read() -> tuple[WindowsDesktopRecord, ...]:
        return (
            WindowsDesktopRecord(
                "native",
                next(paths),
                geometry,
                WallpaperPlacement.FILL,
                (0, 0, 0),
            ),
        )

    provider = WindowsWallpaperProvider(read)

    assert provider.discover((binding,)).default_source.path == first_path
    assert provider.discover((binding,)).default_source.path == second_path
