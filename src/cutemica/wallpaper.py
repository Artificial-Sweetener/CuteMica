from dataclasses import dataclass
from pathlib import Path

from cutemica.enums import WallpaperPlacement
from cutemica.geometry import ScreenBinding


@dataclass(frozen=True, slots=True)
class WallpaperSource:
    path: Path
    placement: WallpaperPlacement
    background_color: tuple[int, int, int] = (0, 0, 0)

    def validate(self) -> None:
        if not self.path.is_file():
            raise FileNotFoundError(f"Wallpaper does not exist: {self.path}")

    @property
    def signature(self) -> str:
        """Return a cache signature without exposing the path in diagnostics."""

        stat = self.path.stat()
        return f"{self.path.resolve()}:{stat.st_size}:{stat.st_mtime_ns}"


@dataclass(frozen=True, slots=True)
class ScreenWallpaper:
    """Associate one wallpaper source with a provider screen identifier."""

    provider_screen_id: str
    source: WallpaperSource


@dataclass(frozen=True, slots=True)
class WallpaperSnapshot:
    """Immutable wallpaper state published atomically by a provider."""

    provider_name: str
    default_source: WallpaperSource
    per_screen: tuple[ScreenWallpaper, ...] = ()

    @classmethod
    def single(cls, provider_name: str, source: WallpaperSource) -> "WallpaperSnapshot":
        """Create a snapshot that applies one source to every display."""

        return cls(provider_name=provider_name, default_source=source)

    def validate(self) -> None:
        self.default_source.validate()
        for item in self.per_screen:
            item.source.validate()

    def source_for(self, binding: ScreenBinding) -> WallpaperSource:
        return next(
            (
                item.source
                for item in self.per_screen
                if item.provider_screen_id == binding.provider_screen_id
            ),
            self.default_source,
        )

    @property
    def display_name(self) -> str:
        sources = {self.default_source.path.name}
        sources.update(item.source.path.name for item in self.per_screen)
        return ", ".join(sorted(sources))


def wallpaper_from_path(
    path: Path,
    placement: WallpaperPlacement = WallpaperPlacement.SPAN,
) -> WallpaperSnapshot:
    """Create and validate an explicitly supplied wallpaper source."""

    source = WallpaperSource(path=path, placement=placement)
    source.validate()
    return WallpaperSnapshot.single("explicit", source)
