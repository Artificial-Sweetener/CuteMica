"""Read the active Orbit desktop wallpaper through its appearance interface."""

from __future__ import annotations

import json
import subprocess
from collections.abc import Callable
from pathlib import Path

from cutemica.enums import WallpaperPlacement
from cutemica.geometry import ScreenBinding
from cutemica.providers.capabilities import ProviderCapabilities
from cutemica.providers.linux_session import linux_window_registration
from cutemica.wallpaper import WallpaperSnapshot, WallpaperSource

CommandRunner = Callable[[tuple[str, ...]], str]


class OrbitWallpaperProvider:
    """Poll Orbit's current image without depending on its private state files."""

    def __init__(self, command: str, *, runner: CommandRunner | None = None) -> None:
        self._command = command
        self._run = runner or _run_command

    @property
    def name(self) -> str:
        return "orbit"

    @property
    def capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(True, True, False, linux_window_registration())

    @property
    def requires_main_thread(self) -> bool:
        return False

    def discover(self, _bindings: tuple[ScreenBinding, ...]) -> WallpaperSnapshot:
        """Resolve the current image afresh so normal polling follows changes."""

        try:
            value: object = json.loads(self._run((self._command, "read")))
        except (ValueError, UnicodeError) as error:
            raise RuntimeError("Orbit returned invalid wallpaper metadata") from error
        if not isinstance(value, dict):
            raise RuntimeError("Orbit returned invalid wallpaper metadata")
        filename = value.get("wallpaper")
        if not isinstance(filename, str) or not Path(filename).is_absolute():
            raise RuntimeError("Orbit did not report an absolute wallpaper filename")
        source = WallpaperSource(Path(filename), WallpaperPlacement.FILL)
        try:
            source.validate()
        except OSError as error:
            # Preserve failure class/errno without putting a private path in reports.
            redacted = type(error)(
                error.errno, "Current wallpaper image is unavailable"
            )
            raise RuntimeError(
                "Orbit's current wallpaper image is unavailable"
            ) from redacted
        return WallpaperSnapshot.single(self.name, source)


def _run_command(arguments: tuple[str, ...]) -> str:
    try:
        completed = subprocess.run(
            arguments, check=True, capture_output=True, text=True, timeout=5
        )
    except (OSError, subprocess.SubprocessError, UnicodeError) as error:
        raise RuntimeError("Could not read Orbit wallpaper metadata") from error
    return completed.stdout
