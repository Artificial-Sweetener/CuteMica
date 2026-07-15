"""KDE Plasma system-theme discovery from its color configuration."""

from __future__ import annotations

import configparser
import os
from pathlib import Path

from cutemica.enums import ResolvedTheme


class KdeThemeProvider:
    """Resolve Plasma color preference from kdeglobals."""

    def __init__(self, config_path: Path | None = None) -> None:
        self._config_path = config_path or _default_config_path()

    @property
    def name(self) -> str:
        return "KDE Plasma system theme"

    def resolve(self) -> ResolvedTheme:
        parser = configparser.ConfigParser(interpolation=None)
        try:
            loaded = parser.read(self._config_path, encoding="utf-8")
        except (configparser.Error, OSError) as error:
            raise RuntimeError(
                "Could not read KDE Plasma color configuration"
            ) from error
        if not loaded:
            raise RuntimeError("Could not read KDE Plasma color configuration")
        background = parser.get(
            "Colors:Window", "BackgroundNormal", fallback=""
        ).strip()
        if background:
            return _theme_for_rgb(background)
        scheme = parser.get("General", "ColorScheme", fallback="")
        if not scheme:
            raise RuntimeError("KDE Plasma color configuration has no color scheme")
        return (
            ResolvedTheme.DARK if "dark" in scheme.casefold() else ResolvedTheme.LIGHT
        )


def _default_config_path() -> Path:
    config_home = os.environ.get("XDG_CONFIG_HOME")
    return (
        Path(config_home) / "kdeglobals"
        if config_home
        else Path.home() / ".config" / "kdeglobals"
    )


def _theme_for_rgb(value: str) -> ResolvedTheme:
    try:
        red, green, blue = (int(channel.strip()) for channel in value.split(",")[:3])
    except (TypeError, ValueError) as error:
        raise RuntimeError("KDE Plasma window color is invalid") from error
    luminance = 0.2126 * red + 0.7152 * green + 0.0722 * blue
    return ResolvedTheme.DARK if luminance < 128 else ResolvedTheme.LIGHT
