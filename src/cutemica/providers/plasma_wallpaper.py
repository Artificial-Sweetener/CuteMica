"""KDE Plasma wallpaper discovery through its read-only scripting API."""

from __future__ import annotations

import json
import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import unquote, urlparse
from urllib.request import url2pathname

from cutemica.enums import WallpaperPlacement
from cutemica.geometry import ScreenBinding
from cutemica.providers.capabilities import ProviderCapabilities
from cutemica.providers.linux_session import linux_window_registration
from cutemica.providers.qt_dbus import qt_dbus_executable
from cutemica.wallpaper import ScreenWallpaper, WallpaperSnapshot, WallpaperSource

CommandRunner = Callable[[tuple[str, ...]], str]
_SCRIPT = """
const result = desktops().map(desktop => {
    const plugin = desktop.wallpaperPlugin;
    desktop.currentConfigGroup = [\"Wallpaper\", plugin, \"General\"];
    return {
        screen: desktop.screen,
        plugin: plugin,
        image: desktop.readConfig(\"Image\", \"\"),
        fillMode: Number(desktop.readConfig(\"FillMode\", 2)),
        color: desktop.readConfig(\"Color\", \"#000000\")
    };
});
print(JSON.stringify(result));
""".strip()


@dataclass(frozen=True, slots=True)
class PlasmaDesktop:
    screen: int
    plugin: str
    image: str
    fill_mode: int
    color: str


class PlasmaWallpaperProvider:
    """Read current per-screen image wallpaper state from Plasma Shell."""

    def __init__(self, runner: CommandRunner | None = None) -> None:
        self._run = runner or _run_plasma_script

    @property
    def name(self) -> str:
        return "kde-plasma"

    @property
    def capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            automatic_wallpaper=True,
            wallpaper_changes=True,
            per_screen_wallpaper=True,
            window_registration=linux_window_registration(),
        )

    @property
    def requires_main_thread(self) -> bool:
        return False

    def discover(self, bindings: tuple[ScreenBinding, ...]) -> WallpaperSnapshot:
        desktops = _parse_desktops(self._run(("plasma", _SCRIPT)))
        screen_sources: list[ScreenWallpaper] = []
        for desktop in desktops:
            if desktop.plugin not in {"org.kde.image", "org.kde.slideshow"}:
                raise RuntimeError(
                    f"Plasma wallpaper plugin {desktop.plugin!r} does not expose "
                    "a current image"
                )
            if desktop.screen < 0 or desktop.screen >= len(bindings):
                continue
            source = WallpaperSource(
                path=_path_from_uri(desktop.image),
                placement=_placement(desktop.fill_mode),
                background_color=_parse_color(desktop.color),
            )
            source.validate()
            screen_sources.append(
                ScreenWallpaper(bindings[desktop.screen].provider_screen_id, source)
            )
        if not screen_sources:
            raise RuntimeError("Plasma did not report a usable desktop wallpaper")
        return WallpaperSnapshot(
            self.name,
            screen_sources[0].source,
            tuple(screen_sources),
        )


def _run_plasma_script(arguments: tuple[str, ...]) -> str:
    command = (
        qt_dbus_executable(),
        "org.kde.plasmashell",
        "/PlasmaShell",
        "org.kde.PlasmaShell.evaluateScript",
        arguments[1],
    )
    try:
        completed = subprocess.run(
            command, check=True, capture_output=True, text=True, timeout=5
        )
    except (OSError, subprocess.SubprocessError) as error:
        raise RuntimeError(f"Could not query Plasma wallpaper: {error}") from error
    return completed.stdout


def _parse_desktops(output: str) -> tuple[PlasmaDesktop, ...]:
    try:
        records = json.loads(output.strip())
    except json.JSONDecodeError as error:
        raise RuntimeError("Plasma returned invalid wallpaper metadata") from error
    if not isinstance(records, list):
        raise RuntimeError("Plasma returned invalid wallpaper metadata")
    return tuple(_desktop_from_record(record) for record in records)


def _desktop_from_record(record: object) -> PlasmaDesktop:
    if not isinstance(record, dict):
        raise RuntimeError("Plasma returned an invalid desktop record")
    try:
        return PlasmaDesktop(
            screen=int(record["screen"]),
            plugin=str(record["plugin"]),
            image=str(record["image"]),
            fill_mode=int(record["fillMode"]),
            color=str(record["color"]),
        )
    except (KeyError, TypeError, ValueError) as error:
        raise RuntimeError("Plasma returned an invalid desktop record") from error


def _path_from_uri(value: str) -> Path:
    parsed = urlparse(value)
    path = parsed.path if parsed.scheme == "file" else value
    return Path(url2pathname(unquote(path)))


def _placement(fill_mode: int) -> WallpaperPlacement:
    return {
        0: WallpaperPlacement.STRETCH,
        1: WallpaperPlacement.FIT,
        2: WallpaperPlacement.FILL,
        3: WallpaperPlacement.TILE,
        4: WallpaperPlacement.TILE,
        5: WallpaperPlacement.TILE,
        6: WallpaperPlacement.CENTER,
    }.get(fill_mode, WallpaperPlacement.FILL)


def _parse_color(value: str) -> tuple[int, int, int]:
    normalized = value.lstrip("#")
    if len(normalized) != 6:
        return 0, 0, 0
    try:
        components = tuple(
            int(normalized[index : index + 2], 16) for index in (0, 2, 4)
        )
    except ValueError:
        return 0, 0, 0
    return components  # type: ignore[return-value]
