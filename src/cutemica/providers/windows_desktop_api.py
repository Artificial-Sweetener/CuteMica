"""Narrow ctypes boundary for the Windows desktop wallpaper API."""

from __future__ import annotations

import ctypes
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from uuid import UUID

from cutemica.enums import WallpaperPlacement
from cutemica.geometry import Rect


@dataclass(frozen=True, slots=True)
class WindowsDesktopRecord:
    """Current wallpaper metadata for one attached Windows monitor."""

    monitor_id: str
    path: Path
    native_geometry_px: Rect
    placement: WallpaperPlacement
    background_color: tuple[int, int, int]


class _Guid(ctypes.Structure):
    _fields_ = [
        ("data1", ctypes.c_uint32),
        ("data2", ctypes.c_uint16),
        ("data3", ctypes.c_uint16),
        ("data4", ctypes.c_ubyte * 8),
    ]

    @classmethod
    def parse(cls, value: str) -> _Guid:
        raw = UUID(value).bytes_le
        return cls.from_buffer_copy(raw)


class _NativeRect(ctypes.Structure):
    _fields_ = [
        ("left", ctypes.c_long),
        ("top", ctypes.c_long),
        ("right", ctypes.c_long),
        ("bottom", ctypes.c_long),
    ]


_CLSID_DESKTOP_WALLPAPER = _Guid.parse("C2CF3110-460E-4FC1-B9D0-8A1C0C9CC4BD")
_IID_DESKTOP_WALLPAPER = _Guid.parse("B92B56A9-8B55-4E14-9A89-0199BBB6F93B")
_PLACEMENTS = {
    0: WallpaperPlacement.CENTER,
    1: WallpaperPlacement.TILE,
    2: WallpaperPlacement.STRETCH,
    3: WallpaperPlacement.FIT,
    4: WallpaperPlacement.FILL,
    5: WallpaperPlacement.SPAN,
}


def read_windows_desktops() -> tuple[WindowsDesktopRecord, ...]:
    """Read the current per-monitor wallpaper paths through IDesktopWallpaper."""

    if sys.platform != "win32":
        raise RuntimeError("Windows desktop wallpaper API requires Windows")
    with _DesktopWallpaper() as desktop:
        placement = _PLACEMENTS.get(desktop.uint_result(11), WallpaperPlacement.FILL)
        background = _color_tuple(desktop.uint_result(9))
        records = tuple(
            record
            for index in range(desktop.uint_result(6))
            if (record := desktop.record(index, placement, background)) is not None
        )
    if not records:
        raise RuntimeError("Windows did not report an image wallpaper")
    return records


class _DesktopWallpaper:
    """Own one COM apartment and IDesktopWallpaper interface pointer."""

    def __init__(self) -> None:
        self._ole32 = ctypes.OleDLL("ole32")
        _configure_ole32(self._ole32)
        self._needs_uninitialize = False
        result = int(self._ole32.CoInitializeEx(None, 2))
        if result in (0, 1):
            self._needs_uninitialize = True
        elif result != -2147417850:  # RPC_E_CHANGED_MODE
            _check_hresult(result, "CoInitializeEx")
        self._interface = ctypes.c_void_p()
        try:
            result = int(
                self._ole32.CoCreateInstance(
                    ctypes.byref(_CLSID_DESKTOP_WALLPAPER),
                    None,
                    0x17,
                    ctypes.byref(_IID_DESKTOP_WALLPAPER),
                    ctypes.byref(self._interface),
                )
            )
            _check_hresult(result, "CoCreateInstance(IDesktopWallpaper)")
        except Exception:
            if self._needs_uninitialize:
                self._ole32.CoUninitialize()
            raise
        self._vtable = ctypes.cast(
            self._interface, ctypes.POINTER(ctypes.POINTER(ctypes.c_void_p))
        ).contents

    def __enter__(self) -> _DesktopWallpaper:
        return self

    def __exit__(self, *_args: object) -> None:
        self._method(2, ctypes.c_ulong)(self._interface)
        if self._needs_uninitialize:
            self._ole32.CoUninitialize()

    def uint_result(self, method_index: int) -> int:
        value = ctypes.c_uint()
        result = self._method(
            method_index, ctypes.c_long, ctypes.POINTER(ctypes.c_uint)
        )(self._interface, ctypes.byref(value))
        _check_hresult(result, f"IDesktopWallpaper method {method_index}")
        return int(value.value)

    def record(
        self,
        index: int,
        placement: WallpaperPlacement,
        background: tuple[int, int, int],
    ) -> WindowsDesktopRecord | None:
        monitor_id = self._string_result(5, ctypes.c_uint(index))
        geometry = _NativeRect()
        result = self._method(
            7, ctypes.c_long, ctypes.c_wchar_p, ctypes.POINTER(_NativeRect)
        )(self._interface, monitor_id, ctypes.byref(geometry))
        if result != 0:
            return None
        _check_hresult(result, "IDesktopWallpaper.GetMonitorRECT")
        path = Path(self._string_result(4, ctypes.c_wchar_p(monitor_id)))
        if not path.is_file():
            return None
        return WindowsDesktopRecord(
            monitor_id,
            path,
            Rect(
                geometry.left,
                geometry.top,
                geometry.right - geometry.left,
                geometry.bottom - geometry.top,
            ),
            placement,
            background,
        )

    def _string_result(self, method_index: int, argument: object) -> str:
        pointer = ctypes.c_void_p()
        result = self._method(
            method_index, ctypes.c_long, type(argument), ctypes.POINTER(ctypes.c_void_p)
        )(self._interface, argument, ctypes.byref(pointer))
        _check_hresult(result, f"IDesktopWallpaper method {method_index}")
        if not pointer.value:
            return ""
        try:
            return ctypes.wstring_at(pointer.value)
        finally:
            self._ole32.CoTaskMemFree(pointer)

    def _method(self, index: int, result: Any, *arguments: Any) -> Any:
        prototype = ctypes.WINFUNCTYPE(result, ctypes.c_void_p, *arguments)
        return prototype(self._vtable[index])


def _check_hresult(result: int, operation: str) -> None:
    if result < 0:
        raise OSError(
            result, f"{operation} failed with HRESULT 0x{result & 0xFFFFFFFF:08X}"
        )


def _color_tuple(colorref: int) -> tuple[int, int, int]:
    return colorref & 0xFF, (colorref >> 8) & 0xFF, (colorref >> 16) & 0xFF


def _configure_ole32(ole32: Any) -> None:
    ole32.CoInitializeEx.argtypes = (ctypes.c_void_p, ctypes.c_uint)
    ole32.CoInitializeEx.restype = ctypes.c_long
    ole32.CoCreateInstance.argtypes = (
        ctypes.POINTER(_Guid),
        ctypes.c_void_p,
        ctypes.c_uint,
        ctypes.POINTER(_Guid),
        ctypes.POINTER(ctypes.c_void_p),
    )
    ole32.CoCreateInstance.restype = ctypes.c_long
    ole32.CoTaskMemFree.argtypes = (ctypes.c_void_p,)
    ole32.CoTaskMemFree.restype = None
    ole32.CoUninitialize.argtypes = ()
    ole32.CoUninitialize.restype = None
