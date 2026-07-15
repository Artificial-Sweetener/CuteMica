from enum import Enum


class ThemeMode(str, Enum):
    AUTO = "auto"
    LIGHT = "light"
    DARK = "dark"


class ResolvedTheme(str, Enum):
    LIGHT = "light"
    DARK = "dark"


class WallpaperPlacement(str, Enum):
    FILL = "fill"
    FIT = "fit"
    STRETCH = "stretch"
    CENTER = "center"
    TILE = "tile"
    SPAN = "span"
