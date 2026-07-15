"""XFCE wallpaper discovery through its native Xfconf channel."""

from __future__ import annotations

import re
import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from cutemica.enums import WallpaperPlacement
from cutemica.geometry import ScreenBinding
from cutemica.providers.capabilities import ProviderCapabilities
from cutemica.providers.linux_session import linux_window_registration
from cutemica.wallpaper import ScreenWallpaper, WallpaperSnapshot, WallpaperSource

CommandRunner = Callable[[tuple[str, ...]], str]
_SETTING_PATTERN = re.compile(
    r"^(?P<base>/backdrop/screen(?P<screen>\d+)/monitor(?P<monitor>[^/]+)/"
    r"workspace(?P<workspace>\d+))/(?P<key>[^/]+)$"
)


@dataclass(frozen=True, slots=True)
class XfceDesktop:
    base: str
    screen: int
    monitor: str
    workspace: int
    image: Path
    image_style: int


class XfceWallpaperProvider:
    """Read per-monitor static wallpaper state from Xfdesktop."""

    def __init__(self, runner: CommandRunner | None = None) -> None:
        self._run = runner or _run_command

    @property
    def name(self) -> str:
        return "xfce"

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
        desktops = _active_workspaces(_parse_settings(self._list_settings()))
        sources = tuple(self._screen_source(item, bindings) for item in desktops)
        if not sources:
            raise RuntimeError("XFCE did not report a usable desktop wallpaper")
        return WallpaperSnapshot(self.name, sources[0].source, sources)

    def _list_settings(self) -> str:
        return self._run(("xfconf-query", "-c", "xfce4-desktop", "-l", "-v"))

    def _screen_source(
        self,
        desktop: XfceDesktop,
        bindings: tuple[ScreenBinding, ...],
    ) -> ScreenWallpaper:
        placement = _placement(desktop.image_style)
        if placement is None:
            raise RuntimeError("XFCE is configured to display a color without an image")
        binding = _binding_for(desktop, bindings)
        source = WallpaperSource(
            path=desktop.image,
            placement=placement,
            background_color=self._background_color(desktop.base),
        )
        source.validate()
        identifier = binding.provider_screen_id if binding else desktop.monitor
        return ScreenWallpaper(identifier, source)

    def _background_color(self, base: str) -> tuple[int, int, int]:
        try:
            output = self._run(
                ("xfconf-query", "-c", "xfce4-desktop", "-p", f"{base}/color1")
            )
        except RuntimeError:
            return 0, 0, 0
        components = tuple(
            int(line) for line in output.splitlines() if line.strip().isdigit()
        )
        if len(components) < 3:
            return 0, 0, 0
        return tuple(round(value * 255 / 65535) for value in components[:3])  # type: ignore[return-value]


def _run_command(arguments: tuple[str, ...]) -> str:
    try:
        completed = subprocess.run(
            arguments,
            check=True,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError) as error:
        raise RuntimeError(f"Could not query XFCE wallpaper: {error}") from error
    return completed.stdout


def _parse_settings(output: str) -> tuple[XfceDesktop, ...]:
    grouped: dict[str, tuple[re.Match[str], dict[str, str]]] = {}
    for line in output.splitlines():
        key, separator, value = line.strip().partition(" ")
        if not separator:
            continue
        match = _SETTING_PATTERN.match(key)
        if match is None:
            continue
        base = match.group("base")
        _, values = grouped.setdefault(base, (match, {}))
        values[match.group("key")] = value.strip()
    desktops: list[XfceDesktop] = []
    for base, (match, values) in grouped.items():
        try:
            desktops.append(
                XfceDesktop(
                    base=base,
                    screen=int(match.group("screen")),
                    monitor=match.group("monitor"),
                    workspace=int(match.group("workspace")),
                    image=Path(values["last-image"]),
                    image_style=int(values["image-style"]),
                )
            )
        except (KeyError, ValueError):
            continue
    return tuple(
        sorted(desktops, key=lambda item: (item.screen, item.monitor, item.workspace))
    )


def _active_workspaces(desktops: tuple[XfceDesktop, ...]) -> tuple[XfceDesktop, ...]:
    selected: dict[tuple[int, str], XfceDesktop] = {}
    for desktop in desktops:
        key = desktop.screen, desktop.monitor.casefold()
        current = selected.get(key)
        if current is None or desktop.workspace < current.workspace:
            selected[key] = desktop
    return tuple(selected.values())


def _binding_for(
    desktop: XfceDesktop,
    bindings: tuple[ScreenBinding, ...],
) -> ScreenBinding | None:
    monitor = _normalized_name(desktop.monitor)
    exact = next(
        (
            binding
            for binding in bindings
            if _normalized_name(binding.qt_screen_name) == monitor
        ),
        None,
    )
    if exact is not None:
        return exact
    return bindings[desktop.screen] if desktop.screen < len(bindings) else None


def _normalized_name(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.casefold())


def _placement(style: int) -> WallpaperPlacement | None:
    return {
        0: None,
        1: WallpaperPlacement.CENTER,
        2: WallpaperPlacement.TILE,
        3: WallpaperPlacement.STRETCH,
        4: WallpaperPlacement.FIT,
        5: WallpaperPlacement.FILL,
        6: WallpaperPlacement.SPAN,
    }.get(style, WallpaperPlacement.FILL)
