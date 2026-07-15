"""Contracts against installed Linux desktop settings implementations."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest
from PIL import Image
from pytestqt.qtbot import QtBot

from cutemica.enums import ResolvedTheme, WallpaperPlacement
from cutemica.geometry import Rect, ScreenBinding
from cutemica.providers.system_theme import create_system_theme_provider
from cutemica.providers.system_wallpaper import create_system_wallpaper_provider
from cutemica.providers.wallpaper_monitor import WallpaperMonitor
from cutemica.theme_monitor import ThemeMonitor

pytestmark = pytest.mark.skipif(
    sys.platform != "linux" or os.environ.get("CUTEMICA_LINUX_CONTRACTS") != "1",
    reason="requires the opt-in Linux desktop contract environment",
)


def test_real_gnome_settings_and_change_monitor(
    monkeypatch: pytest.MonkeyPatch,
    qtbot: QtBot,
    tmp_path: Path,
) -> None:
    first = _wallpaper(tmp_path / "gnome-first.png")
    second = _wallpaper(tmp_path / "gnome-second.png")
    _set_desktop(monkeypatch, "GNOME")
    _set_gsettings("org.gnome.desktop.interface", "color-scheme", "prefer-dark")
    _set_gsettings("org.gnome.desktop.background", "picture-uri", first.as_uri())
    _set_gsettings("org.gnome.desktop.background", "picture-uri-dark", first.as_uri())
    _set_gsettings("org.gnome.desktop.background", "picture-options", "scaled")
    _set_gsettings("org.gnome.desktop.background", "primary-color", "#123abc")
    provider = create_system_wallpaper_provider()
    initial = provider.discover(())

    assert initial.default_source.path == first
    assert initial.default_source.placement is WallpaperPlacement.FIT
    _assert_dark_system_theme()
    monitor = WallpaperMonitor(provider, (), initial)
    _set_gsettings("org.gnome.desktop.background", "picture-uri-dark", second.as_uri())
    with qtbot.waitSignal(monitor.snapshot_changed, timeout=5_000) as changed:
        monitor.poll()

    assert changed.args[0].default_source.path == second
    theme_provider = create_system_theme_provider()
    assert theme_provider is not None
    theme_monitor = ThemeMonitor(theme_provider, ResolvedTheme.DARK)
    _set_gsettings("org.gnome.desktop.interface", "color-scheme", "default")
    with qtbot.waitSignal(theme_monitor.theme_changed, timeout=5_000) as theme_changed:
        theme_monitor.poll()

    assert theme_changed.args == [ResolvedTheme.LIGHT]


def test_real_cinnamon_schema(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    wallpaper = _wallpaper(tmp_path / "cinnamon.png")
    _set_desktop(monkeypatch, "X-Cinnamon")
    _set_gsettings("org.cinnamon.desktop.background", "picture-uri", wallpaper.as_uri())
    _set_gsettings("org.cinnamon.desktop.background", "picture-options", "spanned")
    _set_gsettings("org.cinnamon.desktop.background", "primary-color", "#234567")
    _set_gsettings("org.cinnamon.theme", "name", "Mint-Y-Dark")

    snapshot = create_system_wallpaper_provider().discover(())

    assert snapshot.default_source.path == wallpaper
    assert snapshot.default_source.placement is WallpaperPlacement.SPAN
    _assert_dark_system_theme()


def test_real_mate_schema(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    wallpaper = _wallpaper(tmp_path / "mate.png")
    _set_desktop(monkeypatch, "MATE")
    _set_gsettings("org.mate.background", "picture-filename", str(wallpaper))
    _set_gsettings("org.mate.background", "picture-options", "centered")
    _set_gsettings("org.mate.background", "primary-color", "#345678")
    _set_gsettings("org.mate.interface", "gtk-theme", "BlackMATE")

    snapshot = create_system_wallpaper_provider().discover(())

    assert snapshot.default_source.path == wallpaper
    assert snapshot.default_source.placement is WallpaperPlacement.CENTER
    _assert_dark_system_theme()


def test_real_xfconf_channel(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    wallpaper = _wallpaper(tmp_path / "xfce.png")
    _set_desktop(monkeypatch, "XFCE")
    base = "/backdrop/screen0/monitorVirtual-1/workspace0"
    _set_xfconf(f"{base}/last-image", "string", str(wallpaper))
    _set_xfconf(f"{base}/image-style", "int", "5")
    _set_xfconf_array(f"{base}/color1", (4660, 22136, 39612, 65535))
    _set_xfconf("/Net/ThemeName", "string", "Adwaita-dark", channel="xsettings")
    geometry = Rect(0, 0, 1920, 1080)
    binding = ScreenBinding("virtual", geometry, "Virtual-1", geometry, 1.0)

    snapshot = create_system_wallpaper_provider().discover((binding,))
    source = snapshot.source_for(binding)

    assert source.path == wallpaper
    assert source.placement is WallpaperPlacement.FILL
    assert source.background_color == (18, 86, 154)
    _assert_dark_system_theme()


def test_real_lxqt_profile(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    wallpaper = _wallpaper(tmp_path / "lxqt.png")
    _set_desktop(monkeypatch, "LXQt")
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    profile = tmp_path / "pcmanfm-qt" / "lxqt" / "settings.conf"
    profile.parent.mkdir(parents=True)
    profile.write_text(
        "\n".join(
            (
                "[Desktop]",
                "WallpaperMode=fit",
                f"Wallpaper={wallpaper}",
                "BgColor=#456789",
                "PerScreenWallpaper=true",
            )
        ),
        encoding="utf-8",
    )
    appearance = tmp_path / "lxqt" / "lxqt.conf"
    appearance.parent.mkdir(parents=True)
    appearance.write_text(
        "[General]\ntheme=dark\n[Qt]\nstyle=Fusion\n", encoding="utf-8"
    )

    snapshot = create_system_wallpaper_provider().discover(())

    assert snapshot.default_source.path == wallpaper
    assert snapshot.default_source.placement is WallpaperPlacement.FIT
    _assert_dark_system_theme()


def _wallpaper(path: Path) -> Path:
    Image.new("RGB", (16, 9), (40, 80, 120)).save(path)
    return path


def _set_desktop(monkeypatch: pytest.MonkeyPatch, desktop: str) -> None:
    monkeypatch.setenv("XDG_CURRENT_DESKTOP", desktop)


def _set_gsettings(schema: str, key: str, value: str) -> None:
    _run("gsettings", "set", schema, key, repr(value))


def _set_xfconf(
    property_name: str,
    value_type: str,
    value: str,
    *,
    channel: str = "xfce4-desktop",
) -> None:
    _run(
        "xfconf-query",
        "-c",
        channel,
        "-p",
        property_name,
        "--create",
        "--type",
        value_type,
        "--set",
        value,
    )


def _set_xfconf_array(property_name: str, values: tuple[int, ...]) -> None:
    arguments = [
        "xfconf-query",
        "-c",
        "xfce4-desktop",
        "-p",
        property_name,
        "--create",
    ]
    for value in values:
        arguments.extend(("--type", "uint", "--set", str(value)))
    _run(*arguments)


def _run(*arguments: str) -> str:
    completed = subprocess.run(
        arguments,
        check=True,
        capture_output=True,
        text=True,
        timeout=10,
    )
    return completed.stdout


def _assert_dark_system_theme() -> None:
    provider = create_system_theme_provider()
    assert provider is not None
    assert provider.resolve() is ResolvedTheme.DARK
