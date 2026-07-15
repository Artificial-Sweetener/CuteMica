"""Contract against Plasma on KWin's headless Wayland backend."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import pytest
from PIL import Image

from cutemica.enums import WallpaperPlacement
from cutemica.geometry import Rect, ScreenBinding
from cutemica.providers.capabilities import WindowRegistration
from cutemica.providers.plasma_wallpaper import PlasmaWallpaperProvider

pytestmark = pytest.mark.skipif(
    sys.platform != "linux" or os.environ.get("CUTEMICA_PLASMA_WAYLAND_SESSION") != "1",
    reason="requires an opt-in virtual Plasma Wayland session",
)


def test_plasma_wayland_provider_and_demo(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    wallpaper = tmp_path / "plasma-wayland.png"
    Image.new("RGB", (16, 9), (40, 80, 120)).save(wallpaper)
    runtime = tmp_path / "runtime"
    runtime.mkdir(mode=0o700)
    socket_name = "cutemica-wayland-0"
    environment = os.environ.copy()
    environment.update(
        {
            "KDE_FULL_SESSION": "true",
            "KWIN_COMPOSE": "QPainter",
            "QT_QPA_PLATFORM": "wayland",
            "WAYLAND_DISPLAY": socket_name,
            "XDG_CURRENT_DESKTOP": "KDE",
            "XDG_RUNTIME_DIR": str(runtime),
            "XDG_SESSION_TYPE": "wayland",
        }
    )
    config_home = tmp_path / "config"
    config_home.mkdir()
    _write_dark_kdeglobals(config_home)
    environment["XDG_CONFIG_HOME"] = str(config_home)
    compositor_log_path = tmp_path / "kwin.log"
    shell_log_path = tmp_path / "plasmashell.log"
    compositor_log = compositor_log_path.open("wb", buffering=0)
    shell_log = shell_log_path.open("wb", buffering=0)
    compositor = subprocess.Popen(
        (
            "kwin_wayland",
            "--virtual",
            "--socket",
            socket_name,
            "--width",
            "1920",
            "--height",
            "1080",
            "--no-lockscreen",
            "--no-global-shortcuts",
            "--no-kactivities",
        ),
        env=environment,
        stdout=compositor_log,
        stderr=subprocess.STDOUT,
    )
    shell: subprocess.Popen[bytes] | None = None
    try:
        _wait_for_socket(compositor, runtime / socket_name)
        shell = subprocess.Popen(
            ("plasmashell", "--no-respawn"),
            env=environment,
            stdout=shell_log,
            stderr=subprocess.STDOUT,
        )
        _wait_for_plasma(shell, shell_log_path)
        _evaluate_script(_configure_script(wallpaper))
        monkeypatch.setenv("XDG_SESSION_TYPE", "wayland")
        geometry = Rect(0, 0, 1920, 1080)
        binding = ScreenBinding("virtual", geometry, "Virtual-1", geometry, 1.0)
        provider = PlasmaWallpaperProvider()

        snapshot = provider.discover((binding,))
        source = snapshot.source_for(binding)

        assert source.path == wallpaper
        assert source.placement is WallpaperPlacement.FILL
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
        if shell is not None:
            _stop(shell)
        _stop(compositor)
        shell_log.close()
        compositor_log.close()


def _wait_for_socket(process: subprocess.Popen[bytes], socket: Path) -> None:
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError("KWin exited before creating its Wayland socket")
        if socket.exists():
            return
        time.sleep(0.2)
    raise RuntimeError("KWin did not create its Wayland socket")


def _wait_for_plasma(shell: subprocess.Popen[bytes], log_path: Path) -> None:
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        if shell.poll() is not None:
            raise RuntimeError(
                "Plasma Shell exited before publishing its D-Bus API:\n"
                f"{_log_tail(log_path)}"
            )
        try:
            _evaluate_script("print(desktops().length);")
        except RuntimeError:
            time.sleep(0.2)
            continue
        return
    raise RuntimeError("Plasma Shell did not publish its D-Bus API")


def _log_tail(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")[-4_000:]
    except OSError:
        return "log unavailable"


def _configure_script(wallpaper: Path) -> str:
    return (
        "desktops().forEach(desktop => {"
        'desktop.wallpaperPlugin = "org.kde.image";'
        'desktop.currentConfigGroup = ["Wallpaper", "org.kde.image", "General"];'
        f'desktop.writeConfig("Image", "{wallpaper.as_uri()}");'
        'desktop.writeConfig("FillMode", 2);'
        'desktop.writeConfig("Color", "#123abc");'
        "});"
    )


def _write_dark_kdeglobals(config_home: Path) -> None:
    (config_home / "kdeglobals").write_text(
        "[General]\nColorScheme=BreezeDark\n"
        "[Colors:Window]\nBackgroundNormal=35,38,41\n",
        encoding="utf-8",
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


def _evaluate_script(script: str) -> str:
    executable = next(
        (
            path
            for name in ("qdbus6", "qdbus", "qdbus-qt5")
            if (path := shutil.which(name))
        ),
        None,
    )
    if executable is None:
        raise RuntimeError("Plasma session test requires qdbus")
    try:
        completed = subprocess.run(
            (
                executable,
                "org.kde.plasmashell",
                "/PlasmaShell",
                "org.kde.PlasmaShell.evaluateScript",
                script,
            ),
            check=True,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError) as error:
        raise RuntimeError("Could not call the Plasma scripting API") from error
    return completed.stdout


def _stop(process: subprocess.Popen[bytes]) -> None:
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)
