import json
from pathlib import Path

from PIL import Image
from pytestqt.qtbot import QtBot

from cutemica.providers.orbit_wallpaper import OrbitWallpaperProvider
from cutemica.providers.wallpaper_monitor import WallpaperMonitor


def test_orbit_async_poll_recovers_after_unavailable_metadata(
    qtbot: QtBot, tmp_path: Path
) -> None:
    first, second = tmp_path / "first.png", tmp_path / "second.png"
    for path in (first, second):
        Image.new("RGB", (8, 8)).save(path)
    responses = iter(
        (
            json.dumps({"wallpaper": str(first)}),
            "invalid JSON",
            json.dumps({"wallpaper": str(second)}),
        )
    )
    provider = OrbitWallpaperProvider("appearance", runner=lambda _: next(responses))
    initial = provider.discover(())
    monitor = WallpaperMonitor(provider, (), initial)
    changes: list[object] = []
    monitor.snapshot_changed.connect(changes.append)

    with qtbot.waitSignal(monitor.failed, timeout=2_000):
        monitor.poll()
    assert not changes
    with qtbot.waitSignal(monitor.snapshot_changed, timeout=2_000) as changed:
        monitor.poll()
    assert changed.args[0].default_source.path == second
    assert len(changes) == 1
