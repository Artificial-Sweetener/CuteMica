"""Native contract for AppKit wallpaper changes through CuteMica's monitor."""

from __future__ import annotations

import os
import sys
import time
from dataclasses import dataclass
from importlib import import_module
from pathlib import Path
from typing import Any, cast

import pytest
from PIL import Image
from PySide6.QtWidgets import QApplication

from cutemica.geometry import ScreenBinding
from cutemica.providers.macos_wallpaper import MacOSWallpaperProvider
from cutemica.providers.qt_screens import infer_qt_screen_bindings
from cutemica.providers.wallpaper_monitor import WallpaperMonitor
from cutemica.wallpaper import WallpaperSnapshot

if (
    sys.platform != "darwin"
    or os.environ.get("CUTEMICA_MACOS_WALLPAPER_MUTATION") != "1"
):
    pytest.skip("requires an opt-in mutable macOS desktop", allow_module_level=True)


@dataclass(frozen=True, slots=True)
class DesktopState:
    screen: Any
    url: Any
    options: dict[Any, Any]


def test_appkit_wallpaper_change_reaches_monitor(
    qapp: QApplication,
    tmp_path: Path,
) -> None:
    first = _wallpaper(tmp_path / "first.png", (20, 80, 140))
    second = _wallpaper(tmp_path / "second.png", (140, 50, 90))
    appkit: Any = import_module("AppKit")
    workspace: Any = appkit.NSWorkspace.sharedWorkspace()
    original = _desktop_state(appkit, workspace)
    bindings = infer_qt_screen_bindings(qapp.screens())

    try:
        _set_every_desktop(appkit, workspace, original, first)
        provider = MacOSWallpaperProvider()
        initial = _wait_for_snapshot(qapp, provider, bindings, first)
        monitor = WallpaperMonitor(provider, bindings, initial)
        observed: list[WallpaperSnapshot] = []
        monitor.snapshot_changed.connect(
            lambda value: _record_snapshot(value, observed)
        )

        _set_every_desktop(appkit, workspace, original, second)
        _wait_for_monitor(qapp, monitor, bindings, observed, second)

        assert len(observed) == 1
        assert _uses_path(observed[0], bindings, second)
    finally:
        _restore_desktops(workspace, original)


def test_native_heic_wallpaper_change_reaches_shared_renderer(
    qapp: QApplication,
) -> None:
    desktop_pictures = Path("/System/Library/Desktop Pictures/.wallpapers")
    first = desktop_pictures / "Sequoia Sunrise" / "Sequoia Sunrise.heic"
    second = desktop_pictures / "Sonoma Horizon" / "Sonoma Horizon.heic"
    if not first.is_file() or not second.is_file():
        pytest.skip("host does not contain both native animated wallpaper stills")
    appkit: Any = import_module("AppKit")
    workspace: Any = appkit.NSWorkspace.sharedWorkspace()
    original = _desktop_state(appkit, workspace)
    bindings = infer_qt_screen_bindings(qapp.screens())

    try:
        _set_every_desktop(appkit, workspace, original, first)
        provider = MacOSWallpaperProvider()
        initial = _wait_for_native_snapshot(qapp, provider, bindings, None)
        monitor = WallpaperMonitor(provider, bindings, initial)
        observed: list[WallpaperSnapshot] = []
        monitor.snapshot_changed.connect(
            lambda value: _record_snapshot(value, observed)
        )

        _set_every_desktop(appkit, workspace, original, second)
        changed = _wait_for_native_snapshot(
            qapp,
            provider,
            bindings,
            initial.default_source.path,
        )
        monitor.poll()
        qapp.processEvents()

        assert changed.default_source.source_kind == "macos-native-still"
        with Image.open(changed.default_source.path) as image:
            image.load()
            assert image.width > 0
        assert observed
        assert observed[-1].default_source.path == changed.default_source.path
    finally:
        _restore_desktops(workspace, original)


def _wallpaper(path: Path, color: tuple[int, int, int]) -> Path:
    Image.new("RGB", (64, 36), color).save(path)
    return path


def _desktop_state(appkit: Any, workspace: Any) -> tuple[DesktopState, ...]:
    screens = cast(list[Any], appkit.NSScreen.screens())
    states: list[DesktopState] = []
    for screen in screens:
        url: Any = workspace.desktopImageURLForScreen_(screen)
        if url is None:
            raise RuntimeError("AppKit did not report the original desktop image")
        options = cast(
            dict[Any, Any], workspace.desktopImageOptionsForScreen_(screen) or {}
        )
        states.append(DesktopState(screen, url, options))
    if not states:
        raise RuntimeError("AppKit did not report an active screen")
    return tuple(states)


def _set_every_desktop(
    appkit: Any,
    workspace: Any,
    states: tuple[DesktopState, ...],
    path: Path,
) -> None:
    url: Any = appkit.NSURL.fileURLWithPath_(str(path))
    for state in states:
        _set_desktop(workspace, state.screen, url, state.options)


def _restore_desktops(workspace: Any, states: tuple[DesktopState, ...]) -> None:
    for state in states:
        _set_desktop(workspace, state.screen, state.url, state.options)


def _set_desktop(workspace: Any, screen: Any, url: Any, options: Any) -> None:
    success, error = cast(
        tuple[bool, Any],
        workspace.setDesktopImageURL_forScreen_options_error_(
            url,
            screen,
            options,
            None,
        ),
    )
    if not success:
        raise RuntimeError(f"AppKit rejected the desktop image: {error}")


def _wait_for_snapshot(
    qapp: QApplication,
    provider: MacOSWallpaperProvider,
    bindings: tuple[ScreenBinding, ...],
    expected: Path,
) -> WallpaperSnapshot:
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        qapp.processEvents()
        snapshot = provider.discover(bindings)
        if _uses_path(snapshot, bindings, expected):
            return snapshot
        time.sleep(0.1)
    raise RuntimeError(f"AppKit did not publish {expected.name}")


def _wait_for_monitor(
    qapp: QApplication,
    monitor: WallpaperMonitor,
    bindings: tuple[ScreenBinding, ...],
    observed: list[WallpaperSnapshot],
    expected: Path,
) -> None:
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        monitor.poll()
        qapp.processEvents()
        if observed and _uses_path(observed[-1], bindings, expected):
            return
        time.sleep(0.1)
    raise RuntimeError(f"CuteMica did not publish {expected.name}")


def _wait_for_native_snapshot(
    qapp: QApplication,
    provider: MacOSWallpaperProvider,
    bindings: tuple[ScreenBinding, ...],
    previous: Path | None,
) -> WallpaperSnapshot:
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline:
        qapp.processEvents()
        snapshot = provider.discover(bindings)
        source = snapshot.default_source
        if source.source_kind == "macos-native-still" and source.path != previous:
            return snapshot
        time.sleep(0.1)
    raise RuntimeError("AppKit did not publish the changed native HEIC wallpaper")


def _uses_path(
    snapshot: WallpaperSnapshot,
    bindings: tuple[ScreenBinding, ...],
    expected: Path,
) -> bool:
    return all(snapshot.source_for(binding).path == expected for binding in bindings)


def _record_snapshot(value: object, observed: list[WallpaperSnapshot]) -> None:
    if isinstance(value, WallpaperSnapshot):
        observed.append(value)
