"""Windows per-display wallpaper provider."""

from collections.abc import Callable

from cutemica.geometry import Rect, ScreenBinding
from cutemica.providers.capabilities import (
    ProviderCapabilities,
    WindowRegistration,
)
from cutemica.providers.windows_desktop_api import (
    WindowsDesktopRecord,
    read_windows_desktops,
)
from cutemica.wallpaper import ScreenWallpaper, WallpaperSnapshot, WallpaperSource

DesktopReader = Callable[[], tuple[WindowsDesktopRecord, ...]]


class WindowsWallpaperProvider:
    """Read current Windows wallpaper metadata for every Qt display."""

    def __init__(self, reader: DesktopReader | None = None) -> None:
        self._read = reader or read_windows_desktops

    @property
    def name(self) -> str:
        return "windows-desktop-api"

    @property
    def capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(True, True, True, WindowRegistration.GLOBAL)

    @property
    def requires_main_thread(self) -> bool:
        return False

    def discover(self, bindings: tuple[ScreenBinding, ...]) -> WallpaperSnapshot:
        records = self._read()
        if not records:
            raise RuntimeError("Windows did not report any desktop images")
        sources = tuple(
            ScreenWallpaper(
                binding.provider_screen_id,
                WallpaperSource(
                    record.path,
                    record.placement,
                    record.background_color,
                ),
            )
            for binding, record in _match_records(records, bindings)
        )
        snapshot = WallpaperSnapshot(self.name, sources[0].source, sources)
        snapshot.validate()
        return snapshot


def _match_records(
    records: tuple[WindowsDesktopRecord, ...],
    bindings: tuple[ScreenBinding, ...],
) -> tuple[tuple[ScreenBinding, WindowsDesktopRecord], ...]:
    if not bindings:
        raise RuntimeError("Windows wallpaper discovery requires a screen binding")
    available = list(records)
    matches: list[tuple[ScreenBinding, WindowsDesktopRecord]] = []
    for binding in bindings:
        if not available:
            break
        record = max(
            available,
            key=lambda item: _overlap_area(
                item.native_geometry_px, binding.native_geometry_px
            ),
        )
        available.remove(record)
        matches.append((binding, record))
    if len(matches) != len(bindings):
        raise RuntimeError("Could not associate every Qt screen with a Windows monitor")
    return tuple(matches)


def _overlap_area(first: Rect, second: Rect) -> int:
    width = max(0, min(first.right, second.right) - max(first.x, second.x))
    height = max(0, min(first.bottom, second.bottom) - max(first.y, second.y))
    return width * height
