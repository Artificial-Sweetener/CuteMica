"""XFCE system-theme discovery through Xfconf."""

from __future__ import annotations

import subprocess
from collections.abc import Callable

from cutemica.enums import ResolvedTheme

CommandRunner = Callable[[tuple[str, ...]], str]


class XfceThemeProvider:
    """Read XFCE's selected GTK theme name."""

    def __init__(self, runner: CommandRunner | None = None) -> None:
        self._run = runner or _run_command

    @property
    def name(self) -> str:
        return "XFCE system theme"

    def resolve(self) -> ResolvedTheme:
        name = self._run(("xfconf-query", "-c", "xsettings", "-p", "/Net/ThemeName"))
        return ResolvedTheme.DARK if "dark" in name.casefold() else ResolvedTheme.LIGHT


def _run_command(arguments: tuple[str, ...]) -> str:
    try:
        completed = subprocess.run(
            arguments,
            check=True,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError) as error:
        raise RuntimeError(f"Could not query XFCE theme: {error}") from error
    return completed.stdout.strip()
