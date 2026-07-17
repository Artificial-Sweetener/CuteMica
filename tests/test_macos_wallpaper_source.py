from pathlib import Path

import pytest

from cutemica.enums import WallpaperPlacement
from cutemica.providers.macos_appkit import MacDesktopRecord
from cutemica.providers.macos_wallpaper_source import MacOSWallpaperSourceResolver


def _record(path: Path, source_url: str | None = None) -> MacDesktopRecord:
    return MacDesktopRecord(
        path,
        (0.0, 0.0, 1920.0, 1080.0),
        WallpaperPlacement.FILL,
        (0, 0, 0),
        source_url,
    )


def test_static_pillow_image_remains_direct(tmp_path: Path) -> None:
    wallpaper = tmp_path / "wallpaper.png"
    wallpaper.write_bytes(b"image")
    writer_calls: list[str] = []
    resolver = MacOSWallpaperSourceResolver(
        cache_directory=tmp_path / "cache",
        image_writer=lambda url, destination: _record_call(
            writer_calls, url, destination
        ),
        system_url_reader=lambda: None,
    )

    resolved = resolver.resolve(_record(wallpaper))

    assert resolved.path == wallpaper
    assert resolved.source_kind == "file"
    assert not writer_calls


def test_heic_is_materialized_once_through_native_decoder(tmp_path: Path) -> None:
    wallpaper = tmp_path / "wallpaper.heic"
    wallpaper.write_bytes(b"heic")
    writer_calls: list[str] = []
    resolver = MacOSWallpaperSourceResolver(
        cache_directory=tmp_path / "cache",
        image_writer=lambda url, destination: _write_result(
            writer_calls, url, destination
        ),
        system_url_reader=lambda: None,
    )

    first = resolver.resolve(_record(wallpaper, wallpaper.as_uri()))
    second = resolver.resolve(_record(wallpaper, wallpaper.as_uri()))

    assert first == second
    assert first.path.suffix == ".png"
    assert first.source_kind == "macos-native-still"
    assert writer_calls == [wallpaper.as_uri()]


def test_missing_video_uses_matching_apple_preview(tmp_path: Path) -> None:
    identifier = "7719B48A-2005-4011-9280-2F64EEC6FD91"
    preview_root = tmp_path / "snapshots"
    preview_root.mkdir()
    preview = preview_root / f"asset-preview-{identifier}.jpg"
    preview.write_bytes(b"jpeg")
    missing = tmp_path / f"{identifier}.mov"
    resolver = MacOSWallpaperSourceResolver(
        cache_directory=tmp_path / "cache",
        image_writer=lambda _url, _destination: False,
        system_url_reader=lambda: None,
        preview_roots=(preview_root,),
    )

    resolved = resolver.resolve(_record(missing, missing.as_uri()))

    assert resolved.path == preview
    assert resolved.source_kind == "macos-native-preview"


def test_system_wallpaper_still_recovers_logical_appkit_url(tmp_path: Path) -> None:
    missing = tmp_path / "logical-wallpaper"
    native_movie = tmp_path / "Native Wallpaper.mov"
    native_still = native_movie.with_suffix(".heic")
    native_still.write_bytes(b"heic")
    writer_calls: list[str] = []

    def writer(url: str, destination: Path) -> bool:
        if url != native_still.as_uri():
            return False
        return _write_result(writer_calls, url, destination)

    resolver = MacOSWallpaperSourceResolver(
        cache_directory=tmp_path / "cache",
        image_writer=writer,
        system_url_reader=lambda: native_movie.as_uri(),
    )

    resolved = resolver.resolve(_record(missing, missing.as_uri()))

    assert resolved.path.is_file()
    assert resolved.source_kind == "macos-native-still"
    assert writer_calls == [native_still.as_uri()]


def test_unresolvable_native_source_does_not_disclose_path(tmp_path: Path) -> None:
    private_name = "identifying-wallpaper-name.mov"
    resolver = MacOSWallpaperSourceResolver(
        cache_directory=tmp_path / "cache",
        image_writer=lambda _url, _destination: False,
        system_url_reader=lambda: None,
        preview_roots=(tmp_path / "previews",),
    )

    with pytest.raises(RuntimeError) as failure:
        resolver.resolve(_record(tmp_path / private_name))

    assert private_name not in str(failure.value)
    assert "readable still representation" in str(failure.value)


def _record_call(calls: list[str], url: str, _destination: Path) -> bool:
    calls.append(url)
    return False


def _write_result(calls: list[str], url: str, destination: Path) -> bool:
    calls.append(url)
    destination.write_bytes(b"png")
    return True
