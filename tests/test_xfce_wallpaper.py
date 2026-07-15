from pathlib import Path

from PIL import Image

from cutemica.enums import WallpaperPlacement
from cutemica.geometry import Rect, ScreenBinding
from cutemica.providers.xfce_wallpaper import XfceWallpaperProvider


def _binding(identifier: str, name: str, x: int) -> ScreenBinding:
    geometry = Rect(x, 0, 100, 100)
    return ScreenBinding(identifier, geometry, name, geometry, 1.0)


def test_xfce_discovers_per_monitor_wallpapers(tmp_path: Path) -> None:
    left = tmp_path / "left wallpaper.png"
    right = tmp_path / "right wallpaper.png"
    Image.new("RGB", (8, 8)).save(left)
    Image.new("RGB", (8, 8)).save(right)
    listing = "\n".join(
        (
            "/backdrop/screen0/monitorDP-1/workspace0/image-style  4",
            f"/backdrop/screen0/monitorDP-1/workspace0/last-image   {left}",
            "/backdrop/screen0/monitorHDMI-1/workspace0/image-style  5",
            f"/backdrop/screen0/monitorHDMI-1/workspace0/last-image   {right}",
        )
    )

    def run(arguments: tuple[str, ...]) -> str:
        if arguments[-2:] == ("-l", "-v"):
            return listing
        return "Value is an array with 4 items:\n4660\n22136\n39612\n65535\n"

    bindings = (
        _binding("left", "DP-1", 0),
        _binding("right", "HDMI-1", 100),
    )
    snapshot = XfceWallpaperProvider(run).discover(bindings)

    assert snapshot.source_for(bindings[0]).path == left
    assert snapshot.source_for(bindings[0]).placement is WallpaperPlacement.FIT
    assert snapshot.source_for(bindings[1]).path == right
    assert snapshot.source_for(bindings[1]).placement is WallpaperPlacement.FILL
    assert snapshot.source_for(bindings[0]).background_color == (18, 86, 154)


def test_xfce_uses_lowest_configured_workspace(tmp_path: Path) -> None:
    first = tmp_path / "first.png"
    second = tmp_path / "second.png"
    Image.new("RGB", (8, 8)).save(first)
    Image.new("RGB", (8, 8)).save(second)
    listing = "\n".join(
        (
            "/backdrop/screen0/monitorVirtual-1/workspace1/image-style  5",
            f"/backdrop/screen0/monitorVirtual-1/workspace1/last-image  {second}",
            "/backdrop/screen0/monitorVirtual-1/workspace0/image-style  1",
            f"/backdrop/screen0/monitorVirtual-1/workspace0/last-image  {first}",
        )
    )

    def run(arguments: tuple[str, ...]) -> str:
        return listing if arguments[-2:] == ("-l", "-v") else ""

    snapshot = XfceWallpaperProvider(run).discover(())

    assert snapshot.default_source.path == first
    assert snapshot.default_source.placement is WallpaperPlacement.CENTER
