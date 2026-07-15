"""Contract against Cinnamon on an isolated X11 display."""

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
    sys.platform != "linux" or os.environ.get("CUTEMICA_CINNAMON_X11_SESSION") != "1",
    reason="requires an opt-in Cinnamon X11 session",
)


def test_cinnamon_x11_provider_and_demo(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    wallpaper = tmp_path / "cinnamon-x11.png"
    Image.new("RGB", (16, 9), (40, 80, 120)).save(wallpaper)
    environment = os.environ.copy()
    environment.update(
        {
            "QT_QPA_PLATFORM": "xcb",
            "XDG_CURRENT_DESKTOP": "X-Cinnamon",
            "XDG_SESSION_TYPE": "x11",
        }
    )
    log_path = tmp_path / "cinnamon.log"
    log = log_path.open("wb", buffering=0)
    shell = subprocess.Popen(
        ("cinnamon", "--x11", "--replace", "--sm-disable"),
        env=environment,
        stdout=log,
        stderr=subprocess.STDOUT,
    )
    try:
        _wait_for_window_manager(shell, log_path)
        _set_gsettings(
            "org.cinnamon.desktop.background", "picture-uri", wallpaper.as_uri()
        )
        _set_gsettings("org.cinnamon.desktop.background", "picture-options", "scaled")
        _set_gsettings("org.cinnamon.desktop.background", "primary-color", "#123abc")
        _set_gsettings("org.cinnamon.theme", "name", "Mint-Y-Dark")
        monkeypatch.setenv("XDG_CURRENT_DESKTOP", "X-Cinnamon")
        monkeypatch.setenv("XDG_SESSION_TYPE", "x11")
        geometry = Rect(0, 0, 1920, 1080)
        binding = ScreenBinding("virtual", geometry, "screen", geometry, 1.0)
        provider = GnomeWallpaperProvider()

        snapshot = provider.discover((binding,))

        assert snapshot.default_source.path == wallpaper
        assert snapshot.default_source.placement is WallpaperPlacement.FIT
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


def _wait_for_window_manager(
    process: subprocess.Popen[bytes],
    log_path: Path,
) -> None:
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(
                "Cinnamon exited before becoming the X11 window manager:\n"
                f"{_log_tail(log_path)}"
            )
        if _has_window_manager():
            return
        time.sleep(0.2)
    raise RuntimeError("Cinnamon did not become the X11 window manager")


def _has_window_manager() -> bool:
    try:
        completed = subprocess.run(
            ("xprop", "-root", "_NET_SUPPORTING_WM_CHECK"),
            check=True,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return "window id" in completed.stdout.casefold()


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
