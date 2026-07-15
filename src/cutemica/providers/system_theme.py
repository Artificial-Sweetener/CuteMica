"""Select an operating-system theme provider when Qt lacks integration."""

from __future__ import annotations

import os
import sys

from cutemica.providers.theme_provider import ThemeProvider


def create_system_theme_provider() -> ThemeProvider | None:
    """Create a Linux desktop provider, leaving native Qt platforms untouched."""

    if not sys.platform.startswith("linux"):
        return None
    desktop = os.environ.get("XDG_CURRENT_DESKTOP", "").casefold()
    if "cinnamon" in desktop:
        from cutemica.providers.gsettings_theme import GtkThemeNameProvider

        return GtkThemeNameProvider("org.cinnamon.theme", key="name")
    if "gnome" in desktop or "unity" in desktop:
        from cutemica.providers.gsettings_theme import GnomeThemeProvider

        return GnomeThemeProvider()
    if "mate" in desktop:
        from cutemica.providers.gsettings_theme import GtkThemeNameProvider

        return GtkThemeNameProvider("org.mate.interface")
    if "xfce" in desktop:
        from cutemica.providers.xfce_theme import XfceThemeProvider

        return XfceThemeProvider()
    if "kde" in desktop or "plasma" in desktop:
        from cutemica.providers.kde_theme import KdeThemeProvider

        return KdeThemeProvider()
    if "lxqt" in desktop:
        from cutemica.providers.lxqt_theme import LxqtThemeProvider

        return LxqtThemeProvider()
    return None
