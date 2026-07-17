"""Resolve macOS desktop URLs to stable renderer-readable still images."""

from __future__ import annotations

import re
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from urllib.parse import unquote, urlsplit

from cutemica.providers.macos_appkit import MacDesktopRecord
from cutemica.providers.macos_native_image import (
    read_system_wallpaper_url,
    write_macos_url_as_png,
)

NativeImageWriter = Callable[[str, Path], bool]
SystemURLReader = Callable[[], str | None]

_DIRECT_IMAGE_SUFFIXES = frozenset(
    {
        ".bmp",
        ".gif",
        ".jpeg",
        ".jpg",
        ".pbm",
        ".pgm",
        ".png",
        ".ppm",
        ".tif",
        ".tiff",
        ".webp",
    }
)
_STILL_SUFFIXES = (".heic", ".jpg", ".jpeg", ".png")
_UUID_PATTERN = re.compile(
    r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
    re.IGNORECASE,
)


@dataclass(frozen=True, slots=True)
class ResolvedMacWallpaper:
    """A renderer-readable still and its privacy-safe source classification."""

    path: Path
    source_kind: str


@dataclass(frozen=True, slots=True)
class _Candidate:
    url: str
    path: Path | None


class MacOSWallpaperSourceResolver:
    """Materialize logical, HEIC, or video-backed AppKit wallpaper sources."""

    def __init__(
        self,
        *,
        cache_directory: Path | None = None,
        image_writer: NativeImageWriter = write_macos_url_as_png,
        system_url_reader: SystemURLReader = read_system_wallpaper_url,
        preview_roots: tuple[Path, ...] | None = None,
    ) -> None:
        self._cache_directory = cache_directory or (
            Path.home() / "Library" / "Caches" / "CuteMica" / "wallpaper-stills"
        )
        self._image_writer = image_writer
        self._system_url_reader = system_url_reader
        self._preview_roots = preview_roots or (
            Path("/Library/Application Support/com.apple.idleassetsd/snapshots"),
            Path.home()
            / "Library"
            / "Application Support"
            / "com.apple.idleassetsd"
            / "snapshots",
        )
        self._resolved: dict[str, ResolvedMacWallpaper] = {}

    def resolve(self, record: MacDesktopRecord) -> ResolvedMacWallpaper:
        """Return a stable image path for one AppKit desktop record."""

        if _is_direct_image(record.path):
            return ResolvedMacWallpaper(record.path, "file")

        system_url = self._system_url_reader()
        state_key = _record_state_key(record, system_url)
        previous = self._resolved.get(state_key)
        if previous is not None and previous.path.is_file():
            return previous

        candidates = tuple(self._candidates(record, system_url))
        for candidate in candidates:
            if candidate.path is not None and _is_direct_image(candidate.path):
                resolved = ResolvedMacWallpaper(candidate.path, "macos-native-preview")
                self._resolved[state_key] = resolved
                return resolved
            materialized = self._materialize(candidate)
            if materialized is not None:
                resolved = ResolvedMacWallpaper(materialized, "macos-native-still")
                self._resolved[state_key] = resolved
                return resolved

        raise RuntimeError(
            "macOS reported a wallpaper without a readable still representation; "
            "AppKit decoding and native wallpaper fallbacks were exhausted"
        )

    def _candidates(
        self,
        record: MacDesktopRecord,
        system_url: str | None,
    ) -> Iterable[_Candidate]:
        reported_url = record.source_url or _path_url(record.path)
        yield from _still_candidates(reported_url, record.path)
        yield from self._preview_candidates((reported_url, str(record.path)))

        if system_url and system_url != reported_url:
            yield from _still_candidates(system_url, _path_from_url(system_url))
            yield from self._preview_candidates((system_url,))

    def _preview_candidates(self, values: tuple[str, ...]) -> Iterable[_Candidate]:
        identifiers = {
            match.group(0).upper()
            for value in values
            for match in _UUID_PATTERN.finditer(value)
        }
        for identifier in sorted(identifiers):
            for root in self._preview_roots:
                path = root / f"asset-preview-{identifier}.jpg"
                yield _Candidate(_path_url(path), path)

    def _materialize(self, candidate: _Candidate) -> Path | None:
        if candidate.path is not None and candidate.path.suffix.casefold() == ".mov":
            return None
        destination = self._cache_path(candidate)
        if destination.is_file():
            return destination
        self._cache_directory.mkdir(parents=True, exist_ok=True)
        temporary = destination.with_suffix(".tmp")
        temporary.unlink(missing_ok=True)
        if not self._image_writer(candidate.url, temporary):
            temporary.unlink(missing_ok=True)
            return None
        if not temporary.is_file():
            raise RuntimeError(
                "AppKit reported success without writing a wallpaper still"
            )
        temporary.replace(destination)
        return destination

    def _cache_path(self, candidate: _Candidate) -> Path:
        revision = candidate.url
        if candidate.path is not None and candidate.path.is_file():
            stat = candidate.path.stat()
            revision = f"{revision}:{stat.st_size}:{stat.st_mtime_ns}:{stat.st_ino}"
        digest = sha256(revision.encode("utf-8")).hexdigest()
        return self._cache_directory / f"{digest}.png"


def _still_candidates(url: str, path: Path | None) -> Iterable[_Candidate]:
    if path is not None and path.suffix.casefold() == ".mov":
        for suffix in _STILL_SUFFIXES:
            still = path.with_suffix(suffix)
            yield _Candidate(_path_url(still), still)
    yield _Candidate(url, path)


def _is_direct_image(path: Path) -> bool:
    return path.is_file() and path.suffix.casefold() in _DIRECT_IMAGE_SUFFIXES


def _path_from_url(value: str) -> Path | None:
    parsed = urlsplit(value)
    if parsed.scheme != "file":
        return None
    decoded = unquote(parsed.path)
    if len(decoded) >= 3 and decoded[0] == "/" and decoded[2] == ":":
        decoded = decoded[1:]
    return Path(decoded)


def _path_url(path: Path) -> str:
    return path.resolve().as_uri()


def _record_state_key(record: MacDesktopRecord, system_url: str | None) -> str:
    revision = record.source_url or str(record.path)
    if record.path.is_file():
        stat = record.path.stat()
        revision = f"{revision}:{stat.st_size}:{stat.st_mtime_ns}:{stat.st_ino}"
    return f"{revision}|{system_url or ''}"
