"""Narrow PyObjC boundary for macOS desktop image metadata."""

from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from pathlib import Path
from typing import Any, cast

from cutemica.enums import WallpaperPlacement


@dataclass(frozen=True, slots=True)
class MacDesktopRecord:
    """AppKit desktop metadata converted to Python value types."""

    path: Path
    frame_points: tuple[float, float, float, float]
    placement: WallpaperPlacement
    background_color: tuple[int, int, int]
    source_url: str | None = None


def read_macos_desktops() -> tuple[MacDesktopRecord, ...]:
    """Read every active macOS desktop image on the AppKit main thread."""

    appkit: Any = import_module("AppKit")
    workspace: Any = appkit.NSWorkspace.sharedWorkspace()
    screens = cast(list[Any], appkit.NSScreen.screens())
    return tuple(_read_screen(appkit, workspace, screen) for screen in screens)


def _read_screen(appkit: Any, workspace: Any, screen: Any) -> MacDesktopRecord:
    url: Any = workspace.desktopImageURLForScreen_(screen)
    if url is None:
        raise RuntimeError("AppKit did not report a desktop image for one screen")
    options = cast(
        dict[Any, Any], workspace.desktopImageOptionsForScreen_(screen) or {}
    )
    frame: Any = screen.frame()
    path = Path(cast(str, url.path()))
    scaling = options.get(
        appkit.NSWorkspaceDesktopImageScalingKey,
        appkit.NSImageScaleProportionallyUpOrDown,
    )
    clipping = bool(options.get(appkit.NSWorkspaceDesktopImageAllowClippingKey, False))
    return MacDesktopRecord(
        path=path,
        frame_points=(
            float(frame.origin.x),
            float(frame.origin.y),
            float(frame.size.width),
            float(frame.size.height),
        ),
        placement=_placement(appkit, scaling, clipping),
        background_color=_background_color(appkit, options),
        source_url=cast(str, url.absoluteString()),
    )


def _placement(appkit: Any, scaling: Any, clipping: bool) -> WallpaperPlacement:
    if scaling == appkit.NSImageScaleAxesIndependently:
        return WallpaperPlacement.STRETCH
    if scaling == appkit.NSImageScaleNone:
        return WallpaperPlacement.CENTER
    return WallpaperPlacement.FILL if clipping else WallpaperPlacement.FIT


def _background_color(appkit: Any, options: dict[Any, Any]) -> tuple[int, int, int]:
    color: Any = options.get(appkit.NSWorkspaceDesktopImageFillColorKey)
    if color is None:
        return 0, 0, 0
    converted: Any = color.colorUsingColorSpace_(appkit.NSColorSpace.sRGBColorSpace())
    if converted is None:
        return 0, 0, 0
    return (
        round(float(converted.redComponent()) * 255),
        round(float(converted.greenComponent()) * 255),
        round(float(converted.blueComponent()) * 255),
    )
