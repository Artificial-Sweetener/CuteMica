"""Typed access to desktop settings exposed through GSettings."""

from __future__ import annotations

import ast
import subprocess
from collections.abc import Callable

CommandRunner = Callable[[tuple[str, ...]], str]


class GSettingsClient:
    """Read GSettings values through an injectable command boundary."""

    def __init__(self, runner: CommandRunner | None = None) -> None:
        self._run = runner or _run_command

    def get(self, schema: str, key: str) -> str:
        return self._run(("gsettings", "get", schema, key)).strip()

    def get_optional(self, schema: str, key: str) -> str | None:
        try:
            value = self.get(schema, key)
        except RuntimeError:
            return None
        return value if decode_string(value) else None


def decode_string(value: str) -> str:
    """Decode the GVariant string representation returned by GSettings."""

    try:
        parsed = ast.literal_eval(value)
    except (SyntaxError, ValueError):
        return value.strip("'\"")
    return parsed if isinstance(parsed, str) else str(parsed)


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
        raise RuntimeError(f"Could not query desktop setting: {error}") from error
    return completed.stdout
