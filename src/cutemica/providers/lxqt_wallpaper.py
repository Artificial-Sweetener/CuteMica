"""LXQt wallpaper discovery from the PCManFM-Qt desktop profile."""

from __future__ import annotations

import configparser
import os
from pathlib import Path

from cutemica.enums import WallpaperPlacement
from cutemica.geometry import ScreenBinding
from cutemica.providers.capabilities import ProviderCapabilities
from cutemica.providers.linux_session import linux_window_registration
from cutemica.wallpaper import WallpaperSnapshot, WallpaperSource


class LxqtWallpaperProvider:
    """Read LXQt's shared static wallpaper configuration."""

    def __init__(self, config_path: Path | None = None) -> None:
        self._config_path = config_path

    @property
    def name(self) -> str:
        return "lxqt"

    @property
    def capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            automatic_wallpaper=True,
            wallpaper_changes=True,
            per_screen_wallpaper=False,
            window_registration=linux_window_registration(),
        )

    @property
    def requires_main_thread(self) -> bool:
        return False

    def discover(self, bindings: tuple[ScreenBinding, ...]) -> WallpaperSnapshot:
        config_path = self._config_path or _find_profile()
        settings = _read_desktop_settings(config_path)
        mode = settings.get("wallpapermode", "none").casefold()
        placement = _placement(
            mode,
            per_screen=settings.getboolean("perscreenwallpaper", fallback=False),
            screen_count=len(bindings),
        )
        if placement is None:
            raise RuntimeError("LXQt is configured to display a color without an image")
        source = WallpaperSource(
            path=Path(settings.get("wallpaper", "")),
            placement=placement,
            background_color=_parse_color(settings.get("bgcolor", "#000000")),
        )
        source.validate()
        return WallpaperSnapshot(self.name, source)


def _find_profile() -> Path:
    config_home = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    candidates = [config_home / "pcmanfm-qt" / "lxqt" / "settings.conf"]
    config_dirs = os.environ.get("XDG_CONFIG_DIRS", "/etc/xdg").split(os.pathsep)
    candidates.extend(
        Path(directory) / "pcmanfm-qt" / "lxqt" / "settings.conf"
        for directory in config_dirs
        if directory
    )
    candidates.append(Path("/usr/share/pcmanfm-qt/lxqt/settings.conf"))
    profile = next((path for path in candidates if path.is_file()), None)
    if profile is None:
        raise RuntimeError("Could not locate the LXQt desktop profile")
    return profile


def _read_desktop_settings(path: Path) -> configparser.SectionProxy:
    parser = configparser.ConfigParser(interpolation=None)
    try:
        with path.open(encoding="utf-8") as config_file:
            parser.read_file(config_file)
    except (OSError, configparser.Error) as error:
        raise RuntimeError("Could not read the LXQt desktop profile") from error
    if "Desktop" not in parser:
        raise RuntimeError("LXQt desktop profile has no Desktop section")
    return parser["Desktop"]


def _placement(
    mode: str,
    *,
    per_screen: bool,
    screen_count: int,
) -> WallpaperPlacement | None:
    if mode == "none":
        return None
    if mode == "zoom" and not per_screen and screen_count > 1:
        return WallpaperPlacement.SPAN
    return {
        "stretch": WallpaperPlacement.STRETCH,
        "fit": WallpaperPlacement.FIT,
        "center": WallpaperPlacement.CENTER,
        "tile": WallpaperPlacement.TILE,
        "zoom": WallpaperPlacement.FILL,
    }.get(mode, WallpaperPlacement.STRETCH)


def _parse_color(value: str) -> tuple[int, int, int]:
    normalized = value.strip().lstrip("#")
    if len(normalized) != 6:
        return 0, 0, 0
    try:
        components = tuple(
            int(normalized[index : index + 2], 16) for index in (0, 2, 4)
        )
    except ValueError:
        return 0, 0, 0
    return components  # type: ignore[return-value]
