from pathlib import Path

from cutemica.enums import ResolvedTheme
from cutemica.providers.gsettings_client import GSettingsClient
from cutemica.providers.gsettings_theme import GnomeThemeProvider, GtkThemeNameProvider
from cutemica.providers.kde_theme import KdeThemeProvider
from cutemica.providers.lxqt_theme import LxqtThemeProvider
from cutemica.providers.xfce_theme import XfceThemeProvider


def test_gnome_uses_explicit_color_scheme() -> None:
    client = GSettingsClient(lambda _arguments: "'prefer-dark'")

    assert GnomeThemeProvider(client).resolve() is ResolvedTheme.DARK


def test_gtk_desktops_use_selected_theme_name() -> None:
    client = GSettingsClient(lambda _arguments: "'Mint-Y-Dark-Aqua'")

    provider = GtkThemeNameProvider("org.cinnamon.theme", client=client, key="name")

    assert provider.resolve() is ResolvedTheme.DARK


def test_mate_black_theme_is_dark() -> None:
    client = GSettingsClient(lambda _arguments: "'BlackMATE'")

    provider = GtkThemeNameProvider("org.mate.interface", client=client)

    assert provider.resolve() is ResolvedTheme.DARK


def test_xfce_uses_selected_theme_name() -> None:
    provider = XfceThemeProvider(lambda _arguments: "Adwaita-dark")

    assert provider.resolve() is ResolvedTheme.DARK


def test_kde_uses_window_background_luminance(tmp_path: Path) -> None:
    config = tmp_path / "kdeglobals"
    config.write_text("[Colors:Window]\nBackgroundNormal=35,38,41\n", encoding="utf-8")

    assert KdeThemeProvider(config).resolve() is ResolvedTheme.DARK


def test_lxqt_uses_configured_style_name(tmp_path: Path) -> None:
    config = tmp_path / "lxqt.conf"
    config.write_text("[Qt]\nstyle=Fusion-Dark\n", encoding="utf-8")

    assert LxqtThemeProvider(config).resolve() is ResolvedTheme.DARK


def test_lxqt_uses_desktop_theme_name(tmp_path: Path) -> None:
    config = tmp_path / "lxqt.conf"
    config.write_text("[General]\ntheme=dark\n[Qt]\nstyle=Fusion\n", encoding="utf-8")

    assert LxqtThemeProvider(config).resolve() is ResolvedTheme.DARK
