"""Typed contract for platform system-theme discovery."""

from typing import Protocol

from cutemica.enums import ResolvedTheme


class ThemeProvider(Protocol):
    """Resolve the desktop's current light or dark preference."""

    @property
    def name(self) -> str: ...

    def resolve(self) -> ResolvedTheme: ...
