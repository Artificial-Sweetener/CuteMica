"""Contract against GNOME Shell on an isolated X11 display."""

from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

import pytest
from PIL import Image

from cutemica.enums import WallpaperPlacement
from cutemica.geometry import Rect, ScreenBinding
from cutemica.providers.capabilities import WindowRegistration
from cutemica.providers.gnome_wallpaper import GnomeWallpaperProvider

pytestmark = pytest.mark.skipif(
    sys.platform != "linux" or os.environ.get("CUTEMICA_GNOME_X11_SESSION") != "1",
    reason="requires an opt-in GNOME X11 session",
)


def test_gnome_x11_provider_and_demo(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    wallpaper = tmp_path / "gnome-x11.png"
    Image.new("RGB", (16, 9), (40, 80, 120)).save(wallpaper)
    environment = os.environ.copy()
    environment.update(
        {
            "QT_QPA_PLATFORM": "xcb",
            "XDG_CURRENT_DESKTOP": "GNOME",
            "XDG_SESSION_TYPE": "x11",
        }
    )
    log_path = tmp_path / "gnome-shell.log"
    log = log_path.open("wb", buffering=0)
    shell = subprocess.Popen(
        ("gnome-shell", "--x11", "--replace", "--sm-disable"),
        env=environment,
        stdout=log,
        stderr=subprocess.STDOUT,
    )
    try:
        _wait_for_shell(shell, log_path)
        _set_gsettings("org.gnome.desktop.interface", "color-scheme", "prefer-dark")
        _set_gsettings(
            "org.gnome.desktop.background", "picture-uri", wallpaper.as_uri()
        )
        _set_gsettings(
            "org.gnome.desktop.background", "picture-uri-dark", wallpaper.as_uri()
        )
        _set_gsettings("org.gnome.desktop.background", "picture-options", "zoom")
        monkeypatch.setenv("XDG_CURRENT_DESKTOP", "GNOME")
        monkeypatch.setenv("XDG_SESSION_TYPE", "x11")
        geometry = Rect(0, 0, 1920, 1080)
        binding = ScreenBinding("virtual", geometry, "screen", geometry, 1.0)
        provider = GnomeWallpaperProvider()

        snapshot = provider.discover((binding,))

        assert snapshot.default_source.path == wallpaper
        assert snapshot.default_source.placement is WallpaperPlacement.FILL
        assert provider.capabilities.window_registration is WindowRegistration.GLOBAL
        assert _system_theme(environment) == "Dark"
        completed = subprocess.run(
            (
                sys.executable,
                "-m",
                "cutemica.demo.main",
                "--wallpaper",
                str(wallpaper),
                "--smoke-test",
            ),
            env=environment,
            check=True,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert "CUTEMICA_SMOKE_OK" in completed.stdout
    finally:
        _stop(shell)
        log.close()


def _wait_for_shell(process: subprocess.Popen[bytes], log_path: Path) -> None:
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(
                "GNOME Shell exited before claiming its D-Bus name:\n"
                f"{_log_tail(log_path)}"
            )
        if _shell_owns_bus_name():
            return
        time.sleep(0.2)
    raise RuntimeError("GNOME Shell did not claim its D-Bus name")


def _shell_owns_bus_name() -> bool:
    try:
        completed = subprocess.run(
            (
                "gdbus",
                "call",
                "--session",
                "--dest",
                "org.freedesktop.DBus",
                "--object-path",
                "/org/freedesktop/DBus",
                "--method",
                "org.freedesktop.DBus.NameHasOwner",
                "org.gnome.Shell",
            ),
            check=True,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return "true" in completed.stdout.casefold()


def _set_gsettings(schema: str, key: str, value: str) -> None:
    subprocess.run(
        ("gsettings", "set", schema, key, repr(value)),
        check=True,
        capture_output=True,
        text=True,
        timeout=10,
    )


def _system_theme(environment: dict[str, str]) -> str:
    completed = subprocess.run(
        (sys.executable, str(Path(__file__).with_name("system_theme_probe.py"))),
        env=environment,
        check=True,
        capture_output=True,
        text=True,
        timeout=10,
    )
    return completed.stdout.strip()


def _log_tail(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")[-4_000:]
    except OSError:
        return "log unavailable"


def _stop(process: subprocess.Popen[bytes]) -> None:
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)
