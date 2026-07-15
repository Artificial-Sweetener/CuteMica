"""Typed contract for platform wallpaper discovery."""

from typing import Protocol

from cutemica.geometry import ScreenBinding
from cutemica.providers.capabilities import ProviderCapabilities
from cutemica.wallpaper import WallpaperSnapshot


class WallpaperProvider(Protocol):
    """Discover immutable wallpaper state without decoding image contents."""

    @property
    def name(self) -> str: ...

    @property
    def capabilities(self) -> ProviderCapabilities: ...

    @property
    def requires_main_thread(self) -> bool: ...

    def discover(self, bindings: tuple[ScreenBinding, ...]) -> WallpaperSnapshot: ...
