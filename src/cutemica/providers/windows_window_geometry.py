"""Win32 native-client geometry for stable mixed-DPI window registration."""

from __future__ import annotations

import ctypes
import sys
from ctypes import wintypes

from PySide6.QtWidgets import QWidget

from cutemica.geometry import FloatRect, Rect, WindowGeometry
from cutemica.providers.capabilities import WindowRegistration


class WindowsWindowGeometryProvider:
    @property
    def registration(self) -> WindowRegistration:
        return WindowRegistration.GLOBAL

    def snapshot(self, window: QWidget) -> WindowGeometry:
        """Read the physical client rectangle independently of Qt's handoff state."""

        native = read_client_rect_px(int(window.window().winId()))
        return WindowGeometry(
            FloatRect(native.x, native.y, native.width, native.height),
            window.width(),
            window.height(),
        )


if sys.platform == "win32":
    _USER32 = ctypes.WinDLL("user32", use_last_error=True)
    _GET_CLIENT_RECT = _USER32.GetClientRect
    _GET_CLIENT_RECT.argtypes = (wintypes.HWND, ctypes.POINTER(wintypes.RECT))
    _GET_CLIENT_RECT.restype = wintypes.BOOL
    _CLIENT_TO_SCREEN = _USER32.ClientToScreen
    _CLIENT_TO_SCREEN.argtypes = (wintypes.HWND, ctypes.POINTER(wintypes.POINT))
    _CLIENT_TO_SCREEN.restype = wintypes.BOOL

    def read_client_rect_px(window_handle: int) -> Rect:
        """Read one top-level client rectangle in physical desktop pixels."""

        handle = wintypes.HWND(window_handle)
        client_rect = wintypes.RECT()
        if not _GET_CLIENT_RECT(handle, ctypes.byref(client_rect)):
            raise ctypes.WinError(ctypes.get_last_error())
        origin = wintypes.POINT()
        if not _CLIENT_TO_SCREEN(handle, ctypes.byref(origin)):
            raise ctypes.WinError(ctypes.get_last_error())
        return Rect(
            origin.x,
            origin.y,
            client_rect.right - client_rect.left,
            client_rect.bottom - client_rect.top,
        )

else:

    def read_client_rect_px(_window_handle: int) -> Rect:
        raise RuntimeError("Win32 client geometry requires Windows")
