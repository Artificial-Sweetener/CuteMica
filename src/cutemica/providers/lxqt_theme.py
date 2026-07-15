"""LXQt system-theme discovery from its Qt palette configuration."""

from __future__ import annotations

import configparser
import os
from pathlib import Path

from cutemica.enums import ResolvedTheme


class LxqtThemeProvider:
    """Resolve LXQt color preference from its configured window palette."""

    def __init__(self, config_path: Path | None = None) -> None:
        self._config_path = config_path or _default_config_path()

    @property
    def name(self) -> str:
        return "LXQt system theme"

    def resolve(self) -> ResolvedTheme:
        parser = configparser.ConfigParser(interpolation=None)
        try:
            loaded = parser.read(self._config_path, encoding="utf-8")
        except (configparser.Error, OSError) as error:
            raise RuntimeError(
                "Could not read LXQt appearance configuration"
            ) from error
        if not loaded:
            raise RuntimeError("Could not read LXQt appearance configuration")
        desktop_theme = parser.get("General", "theme", fallback="")
        if desktop_theme:
            return _theme_from_name(desktop_theme)
        for section in ("Palette", "Qt"):
            for key in ("window", "Window", "active"):
                value = parser.get(section, key, fallback="")
                theme = _theme_from_color(value)
                if theme is not None:
                    return theme
        style = parser.get("Qt", "style", fallback="")
        return _theme_from_name(style)


def _default_config_path() -> Path:
    config_home = os.environ.get("XDG_CONFIG_HOME")
    base = Path(config_home) if config_home else Path.home() / ".config"
    return base / "lxqt" / "lxqt.conf"


def _theme_from_color(value: str) -> ResolvedTheme | None:
    numbers = [part.strip() for part in value.replace("@Variant(", "").split(",")]
    try:
        channels = [int(part) for part in numbers if part.isdigit()]
    except ValueError:
        return None
    if len(channels) < 3:
        return None
    red, green, blue = channels[-3:]
    luminance = 0.2126 * red + 0.7152 * green + 0.0722 * blue
    return ResolvedTheme.DARK if luminance < 128 else ResolvedTheme.LIGHT


def _theme_from_name(name: str) -> ResolvedTheme:
    normalized = name.casefold()
    return (
        ResolvedTheme.DARK
        if any(marker in normalized for marker in ("dark", "black", "noir"))
        else ResolvedTheme.LIGHT
    )
