"""macOS per-display wallpaper provider."""

from collections.abc import Callable

from cutemica.geometry import Rect, ScreenBinding
from cutemica.providers.capabilities import (
    ProviderCapabilities,
    WindowRegistration,
)
from cutemica.providers.macos_appkit import MacDesktopRecord, read_macos_desktops
from cutemica.wallpaper import ScreenWallpaper, WallpaperSnapshot, WallpaperSource

DesktopReader = Callable[[], tuple[MacDesktopRecord, ...]]


class MacOSWallpaperProvider:
    """Read AppKit wallpaper source and placement for every Qt display."""

    def __init__(self, reader: DesktopReader | None = None) -> None:
        self._read = reader or read_macos_desktops

    @property
    def name(self) -> str:
        return "macos-appkit"

    @property
    def capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(True, True, True, WindowRegistration.GLOBAL)

    @property
    def requires_main_thread(self) -> bool:
        return True

    def discover(self, bindings: tuple[ScreenBinding, ...]) -> WallpaperSnapshot:
        records = self._read()
        if not records:
            raise RuntimeError("AppKit did not report any desktop images")
        matches = _match_records(records, bindings)
        sources = tuple(
            ScreenWallpaper(
                binding.provider_screen_id,
                WallpaperSource(
                    record.path,
                    record.placement,
                    record.background_color,
                ),
            )
            for binding, record in matches
        )
        snapshot = WallpaperSnapshot(self.name, sources[0].source, sources)
        snapshot.validate()
        return snapshot


def _match_records(
    records: tuple[MacDesktopRecord, ...],
    bindings: tuple[ScreenBinding, ...],
) -> tuple[tuple[ScreenBinding, MacDesktopRecord], ...]:
    if not bindings:
        raise RuntimeError("macOS wallpaper discovery requires a screen binding")
    main_height = records[0].frame_points[3]
    available = list(records)
    matches: list[tuple[ScreenBinding, MacDesktopRecord]] = []
    for binding in bindings:
        record = next(
            (
                item
                for item in available
                if _qt_geometry(item, main_height) == binding.qt_geometry_dip
            ),
            None,
        )
        if record is None:
            if not available:
                break
            record = available[0]
        available.remove(record)
        matches.append((binding, record))
    if len(matches) != len(bindings):
        raise RuntimeError("Could not associate every Qt screen with an AppKit screen")
    return tuple(matches)


def _qt_geometry(record: MacDesktopRecord, main_height: float) -> Rect:
    x, y, width, height = record.frame_points
    return Rect(
        round(x),
        round(main_height - y - height),
        round(width),
        round(height),
    )
