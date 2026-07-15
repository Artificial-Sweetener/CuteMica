"""Fast, provider-independent Mica Alt rendering for PySide6."""

from cutemica.enums import ResolvedTheme, ThemeMode
from cutemica.recipe import MicaAltRecipe
from cutemica.wallpaper import WallpaperSnapshot, WallpaperSource, wallpaper_from_path

__all__ = [
    "MicaAltRecipe",
    "ResolvedTheme",
    "ThemeMode",
    "WallpaperSnapshot",
    "WallpaperSource",
    "wallpaper_from_path",
]

__version__ = "0.1.0"
