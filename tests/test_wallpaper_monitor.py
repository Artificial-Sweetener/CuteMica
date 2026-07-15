from pathlib import Path

from PIL import Image
from PySide6.QtCore import QObject
from pytestqt.qtbot import QtBot

from cutemica.enums import WallpaperPlacement
from cutemica.providers.capabilities import (
    ProviderCapabilities,
    WindowRegistration,
)
from cutemica.providers.wallpaper_monitor import WallpaperMonitor
from cutemica.wallpaper import WallpaperSnapshot, WallpaperSource


class SequenceProvider:
    def __init__(self, snapshots: list[WallpaperSnapshot]) -> None:
        self._snapshots = snapshots

    @property
    def name(self) -> str:
        return "sequence"

    @property
    def capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(True, True, False, WindowRegistration.GLOBAL)

    @property
    def requires_main_thread(self) -> bool:
        return True

    def discover(self, _bindings: object) -> WallpaperSnapshot:
        return self._snapshots.pop(0)


def test_monitor_publishes_only_changed_snapshots(qtbot: QtBot, tmp_path: Path) -> None:
    first_path = tmp_path / "first.png"
    second_path = tmp_path / "second.png"
    Image.new("RGB", (8, 8)).save(first_path)
    Image.new("RGB", (8, 8)).save(second_path)
    first = WallpaperSnapshot.single(
        "test", WallpaperSource(first_path, WallpaperPlacement.FILL)
    )
    second = WallpaperSnapshot.single(
        "test", WallpaperSource(second_path, WallpaperPlacement.FILL)
    )
    owner = QObject()
    monitor = WallpaperMonitor(
        SequenceProvider([first, second]), (), first, parent=owner
    )

    monitor.poll()
    with qtbot.assertNotEmitted(monitor.snapshot_changed):
        pass
    with qtbot.waitSignal(monitor.snapshot_changed, timeout=500) as changed:
        monitor.poll()

    assert changed.args == [second]
