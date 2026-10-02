"""Identify an Orbit wallpaper owner in the current Linux desktop session."""

from __future__ import annotations

import os
import re
import shutil
from pathlib import Path

_PROC_ROOT = Path("/proc")


def orbit_appearance_command() -> str | None:
    """Return Orbit's reader only when Orbit owns this user's display."""

    command = shutil.which("o-computer-appearance")
    if command is None:
        return None
    desktop_names = os.environ.get("XDG_CURRENT_DESKTOP", "").casefold().split(":")
    if "orbit" in desktop_names:
        return command
    session_type = os.environ.get("XDG_SESSION_TYPE", "").casefold()
    wayland = session_type == "wayland" or (
        not session_type and bool(os.environ.get("WAYLAND_DISPLAY"))
    )
    display_key = "WAYLAND_DISPLAY" if wayland else "DISPLAY"
    display = os.environ.get(display_key, "")
    identity = _display_name(
        display, display_key, os.environ.get("XDG_RUNTIME_DIR", "")
    )
    if identity is None:
        return None
    try:
        processes = tuple(_PROC_ROOT.iterdir())
    except OSError:
        return None
    for process in processes:
        if not process.name.isdecimal():
            continue
        try:
            if process.stat().st_uid != os.getuid():
                continue
            if (process / "comm").read_text().strip() != "orbit-desktop":
                continue
            environment = (process / "environ").read_bytes().split(b"\0")
        except (OSError, UnicodeError):
            continue
        if (
            _display_name(
                _environment_value(environment, display_key),
                display_key,
                _environment_value(environment, "XDG_RUNTIME_DIR"),
            )
            == identity
        ):
            return command
    return None


def _environment_value(environment: list[bytes], key: str) -> str:
    prefix = os.fsencode(key + "=")
    return os.fsdecode(
        next(
            (item[len(prefix) :] for item in environment if item.startswith(prefix)),
            b"",
        )
    )


def _display_name(value: str, key: str, runtime_directory: str) -> str | None:
    if not value:
        return None
    if key == "DISPLAY":
        return re.sub(r"(:\d+)\.\d+$", r"\1", value)
    socket = Path(value)
    if socket.is_absolute():
        return os.path.normpath(socket)
    if not Path(runtime_directory).is_absolute():
        return None
    return os.path.normpath(Path(runtime_directory) / socket)
