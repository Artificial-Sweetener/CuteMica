"""Capabilities reported by platform environment providers."""

from dataclasses import dataclass
from enum import StrEnum


class WindowRegistration(StrEnum):
    """Level of desktop registration exposed by the window system."""

    GLOBAL = "global"
    SCREEN_LOCAL = "screen-local"


@dataclass(frozen=True, slots=True)
class ProviderCapabilities:
    """Observable behavior supported by one wallpaper provider."""

    automatic_wallpaper: bool
    wallpaper_changes: bool
    per_screen_wallpaper: bool
    window_registration: WindowRegistration
