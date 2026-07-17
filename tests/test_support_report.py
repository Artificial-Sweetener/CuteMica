import json
from pathlib import Path

from cutemica.diagnostics.report import build_support_report
from cutemica.diagnostics.session import ValidationSession
from cutemica.enums import ResolvedTheme, WallpaperPlacement
from cutemica.geometry import Rect, ScreenBinding
from cutemica.wallpaper import ScreenWallpaper, WallpaperSnapshot, WallpaperSource


def test_report_describes_multiple_wallpapers_without_identifying_them(
    tmp_path: Path,
) -> None:
    left_path = tmp_path / "private-left-name.jpg"
    right_path = tmp_path / "private-right-name.jpg"
    left_path.write_bytes(b"left")
    right_path.write_bytes(b"right")
    bindings = (_binding("left", 0), _binding("right", 1920))
    left = WallpaperSource(left_path, WallpaperPlacement.FILL)
    right = WallpaperSource(right_path, WallpaperPlacement.FILL)
    wallpaper = WallpaperSnapshot(
        "macos-appkit",
        left,
        (
            ScreenWallpaper("left", left),
            ScreenWallpaper("right", right),
        ),
    )
    session = ValidationSession(bindings, ResolvedTheme.DARK, "macos-appkit")

    report = build_support_report(session, bindings, wallpaper, "global")
    serialized = json.dumps(report)

    assert report["wallpaper"] == {
        "provider": "macos-appkit",
        "per_screen_assignments": 2,
        "source_count": 2,
        "sources": [{"file_type": ".jpg", "placement": "fill", "source_kind": "file"}],
        "privacy": "Wallpaper pixels, filenames, and paths are not collected.",
    }
    assert "private-left-name" not in serialized
    assert "private-right-name" not in serialized
    assert str(tmp_path) not in serialized


def _binding(identifier: str, x: int) -> ScreenBinding:
    geometry = Rect(x, 0, 1920, 1080)
    return ScreenBinding(identifier, geometry, identifier.title(), geometry, 1)
