"""Contract against GNOME Shell's headless Wayland backend."""

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
    sys.platform != "linux" or os.environ.get("CUTEMICA_GNOME_WAYLAND_SESSION") != "1",
    reason="requires an opt-in headless GNOME Wayland session",
)


def test_gnome_wayland_provider_and_demo(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    wallpaper = tmp_path / "gnome-wayland.png"
    Image.new("RGB", (16, 9), (40, 80, 120)).save(wallpaper)
    runtime = tmp_path / "runtime"
    runtime.mkdir(mode=0o700)
    socket_name = "cutemica-gnome-0"
    environment = os.environ.copy()
    environment.update(
        {
            "QT_QPA_PLATFORM": "wayland",
            "WAYLAND_DISPLAY": socket_name,
            "XDG_CURRENT_DESKTOP": "GNOME",
            "XDG_RUNTIME_DIR": str(runtime),
            "XDG_SESSION_TYPE": "wayland",
        }
    )
    log_path = tmp_path / "gnome-shell.log"
    log = log_path.open("wb", buffering=0)
    shell_command = [
        "gnome-shell",
        "--wayland",
        "--headless",
        "--no-x11",
        "--wayland-display",
        socket_name,
        "--virtual-monitor",
        "1920x1080",
    ]
    if _gnome_shell_supports("--sm-disable"):
        shell_command.append("--sm-disable")
    shell = subprocess.Popen(
        tuple(shell_command),
        env=environment,
        stdout=log,
        stderr=subprocess.STDOUT,
    )
    try:
        _wait_for_socket(shell, runtime / socket_name, log_path)
        _set_gsettings("org.gnome.desktop.interface", "color-scheme", "prefer-dark")
        _set_gsettings(
            "org.gnome.desktop.background", "picture-uri", wallpaper.as_uri()
        )
        _set_gsettings(
            "org.gnome.desktop.background", "picture-uri-dark", wallpaper.as_uri()
        )
        _set_gsettings("org.gnome.desktop.background", "picture-options", "scaled")
        _set_gsettings("org.gnome.desktop.background", "primary-color", "#123abc")
        monkeypatch.setenv("XDG_CURRENT_DESKTOP", "GNOME")
        monkeypatch.setenv("XDG_SESSION_TYPE", "wayland")
        geometry = Rect(0, 0, 1920, 1080)
        binding = ScreenBinding("virtual", geometry, "Virtual-1", geometry, 1.0)
        provider = GnomeWallpaperProvider()

        snapshot = provider.discover((binding,))

        assert snapshot.default_source.path == wallpaper
        assert snapshot.default_source.placement is WallpaperPlacement.FIT
        assert (
            provider.capabilities.window_registration is WindowRegistration.SCREEN_LOCAL
        )
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


def _wait_for_socket(
    process: subprocess.Popen[bytes],
    socket: Path,
    log_path: Path,
) -> None:
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(
                "GNOME Shell exited before creating its Wayland socket:\n"
                f"{_log_tail(log_path)}"
            )
        if socket.exists():
            return
        time.sleep(0.2)
    raise RuntimeError("GNOME Shell did not create its Wayland socket")


def _set_gsettings(schema: str, key: str, value: str) -> None:
    subprocess.run(
        ("gsettings", "set", schema, key, repr(value)),
        check=True,
        capture_output=True,
        text=True,
        timeout=10,
    )


def _gnome_shell_supports(option: str) -> bool:
    completed = subprocess.run(
        ("gnome-shell", "--help"),
        check=True,
        capture_output=True,
        text=True,
        timeout=10,
    )
    return option in f"{completed.stdout}\n{completed.stderr}"


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
