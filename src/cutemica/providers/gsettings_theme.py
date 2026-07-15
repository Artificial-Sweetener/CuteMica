"""System-theme discovery for GSettings-based desktops."""

from __future__ import annotations

from cutemica.enums import ResolvedTheme
from cutemica.providers.gsettings_client import GSettingsClient, decode_string


class GnomeThemeProvider:
    """Read GNOME's explicit system color-scheme preference."""

    def __init__(self, client: GSettingsClient | None = None) -> None:
        self._settings = client or GSettingsClient()

    @property
    def name(self) -> str:
        return "GNOME system theme"

    def resolve(self) -> ResolvedTheme:
        value = self._settings.get(
            "org.gnome.desktop.interface", "color-scheme"
        ).casefold()
        return ResolvedTheme.DARK if "dark" in value else ResolvedTheme.LIGHT


class GtkThemeNameProvider:
    """Infer color preference from a desktop's selected GTK theme."""

    def __init__(
        self,
        schema: str,
        *,
        client: GSettingsClient | None = None,
        key: str = "gtk-theme",
    ) -> None:
        self._schema = schema
        self._key = key
        self._settings = client or GSettingsClient()

    @property
    def name(self) -> str:
        return f"{self._schema} system theme"

    def resolve(self) -> ResolvedTheme:
        theme_name = decode_string(self._settings.get(self._schema, self._key))
        return (
            ResolvedTheme.DARK if _dark_theme_name(theme_name) else ResolvedTheme.LIGHT
        )


def _dark_theme_name(theme_name: str) -> bool:
    normalized = theme_name.casefold().replace("_", "-")
    return any(marker in normalized for marker in ("dark", "black", "noir"))
