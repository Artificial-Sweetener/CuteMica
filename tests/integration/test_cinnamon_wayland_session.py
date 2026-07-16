"""Contract against Cinnamon nested in a headless Wayland compositor."""

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
from tests.integration.dbus_environment import update_dbus_activation_environment

pytestmark = pytest.mark.skipif(
    sys.platform != "linux"
    or os.environ.get("CUTEMICA_CINNAMON_WAYLAND_SESSION") != "1",
    reason="requires an opt-in nested Cinnamon Wayland session",
)


def test_cinnamon_wayland_provider_and_demo(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    wallpaper = tmp_path / "cinnamon-wayland.png"
    Image.new("RGB", (16, 9), (40, 80, 120)).save(wallpaper)
    runtime = tmp_path / "runtime"
    runtime.mkdir(mode=0o700)
    parent_socket = "cutemica-parent-0"
    base_environment = os.environ.copy()
    base_environment.update(
        {
            "XDG_CURRENT_DESKTOP": "X-Cinnamon",
            "XDG_RUNTIME_DIR": str(runtime),
            "XDG_SESSION_TYPE": "wayland",
        }
    )
    compositor_environment = base_environment | {
        "KWIN_COMPOSE": "QPainter",
        "WAYLAND_DISPLAY": parent_socket,
    }
    compositor_log_path = tmp_path / "kwin.log"
    cinnamon_log_path = tmp_path / "cinnamon.log"
    compositor_log = compositor_log_path.open("wb", buffering=0)
    cinnamon_log = cinnamon_log_path.open("wb", buffering=0)
    compositor = subprocess.Popen(
        (
            "kwin_wayland",
            "--virtual",
            "--socket",
            parent_socket,
            "--width",
            "1920",
            "--height",
            "1080",
            "--no-lockscreen",
            "--no-global-shortcuts",
            "--no-kactivities",
        ),
        env=compositor_environment,
        stdout=compositor_log,
        stderr=subprocess.STDOUT,
    )
    cinnamon: subprocess.Popen[bytes] | None = None
    try:
        _wait_for_socket(compositor, runtime / parent_socket, compositor_log_path)
        cinnamon_environment = base_environment | {
            "WAYLAND_DISPLAY": parent_socket,
        }
        cinnamon = subprocess.Popen(
            (
                "cinnamon",
                "--wayland",
                "--nested",
                "--no-x11",
                "--sm-disable",
            ),
            env=cinnamon_environment,
            stdout=cinnamon_log,
            stderr=subprocess.STDOUT,
        )
        child_socket = _wait_for_child_socket(
            cinnamon,
            runtime,
            parent_socket,
            cinnamon_log_path,
        )
        _set_gsettings(
            "org.cinnamon.desktop.background", "picture-uri", wallpaper.as_uri()
        )
        _set_gsettings("org.cinnamon.desktop.background", "picture-options", "zoom")
        _set_gsettings("org.cinnamon.theme", "name", "Mint-Y-Dark")
        monkeypatch.setenv("XDG_CURRENT_DESKTOP", "X-Cinnamon")
        monkeypatch.setenv("XDG_SESSION_TYPE", "wayland")
        geometry = Rect(0, 0, 1920, 1080)
        binding = ScreenBinding("virtual", geometry, "Virtual-1", geometry, 1.0)
        provider = GnomeWallpaperProvider()

        snapshot = provider.discover((binding,))

        assert snapshot.default_source.path == wallpaper
        assert snapshot.default_source.placement is WallpaperPlacement.FILL
        assert (
            provider.capabilities.window_registration is WindowRegistration.SCREEN_LOCAL
        )
        demo_environment = base_environment | {
            "QT_QPA_PLATFORM": "wayland",
            "WAYLAND_DISPLAY": child_socket,
        }
        update_dbus_activation_environment(
            demo_environment,
            (
                "QT_QPA_PLATFORM",
                "WAYLAND_DISPLAY",
                "XDG_CURRENT_DESKTOP",
                "XDG_RUNTIME_DIR",
                "XDG_SESSION_TYPE",
            ),
        )
        assert _system_theme(demo_environment) == "Dark"
        completed = subprocess.run(
            (
                sys.executable,
                "-m",
                "cutemica.demo.main",
                "--wallpaper",
                str(wallpaper),
                "--smoke-test",
            ),
            env=demo_environment,
            check=True,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert "CUTEMICA_SMOKE_OK" in completed.stdout
    finally:
        if cinnamon is not None:
            _stop(cinnamon)
        _stop(compositor)
        cinnamon_log.close()
        compositor_log.close()


def _wait_for_socket(
    process: subprocess.Popen[bytes],
    socket: Path,
    log_path: Path,
) -> None:
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        _raise_if_exited(process, log_path)
        if socket.exists():
            return
        time.sleep(0.2)
    raise RuntimeError("Parent compositor did not create its Wayland socket")


def _wait_for_child_socket(
    process: subprocess.Popen[bytes],
    runtime: Path,
    parent_socket: str,
    log_path: Path,
) -> str:
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        _raise_if_exited(process, log_path)
        sockets = tuple(
            path.name
            for path in runtime.glob("wayland-*")
            if not path.name.endswith(".lock") and path.name != parent_socket
        )
        if sockets:
            return sockets[0]
        time.sleep(0.2)
    raise RuntimeError("Cinnamon did not create its nested Wayland socket")


def _raise_if_exited(process: subprocess.Popen[bytes], log_path: Path) -> None:
    if process.poll() is not None:
        raise RuntimeError(
            f"Desktop process exited unexpectedly:\n{_log_tail(log_path)}"
        )


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
