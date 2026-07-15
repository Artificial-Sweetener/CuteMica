"""Contract against a real Plasma Shell session on an isolated display."""

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
from cutemica.providers.plasma_wallpaper import PlasmaWallpaperProvider

pytestmark = pytest.mark.skipif(
    sys.platform != "linux" or os.environ.get("CUTEMICA_PLASMA_SESSION") != "1",
    reason="requires an opt-in Plasma desktop session",
)


def test_plasma_shell_reports_configured_wallpaper(tmp_path: Path) -> None:
    wallpaper = tmp_path / "plasma.png"
    Image.new("RGB", (16, 9), (40, 80, 120)).save(wallpaper)
    environment = os.environ.copy()
    environment.update(
        {
            "KDE_FULL_SESSION": "true",
            "QT_QPA_PLATFORM": "xcb",
            "XDG_CURRENT_DESKTOP": "KDE",
            "XDG_SESSION_TYPE": "x11",
        }
    )
    config_home = tmp_path / "config"
    config_home.mkdir()
    _write_dark_kdeglobals(config_home)
    environment["XDG_CONFIG_HOME"] = str(config_home)
    shell = subprocess.Popen(
        ("plasmashell", "--no-respawn"),
        env=environment,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        _wait_for_plasma(shell)
        _evaluate_script(_configure_script(wallpaper))
        geometry = Rect(0, 0, 1920, 1080)
        binding = ScreenBinding("virtual", geometry, "screen", geometry, 1.0)

        snapshot = PlasmaWallpaperProvider().discover((binding,))
        source = snapshot.source_for(binding)

        assert source.path == wallpaper
        assert source.placement is WallpaperPlacement.FILL
        assert source.background_color == (0x12, 0x3A, 0xBC)
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
        shell.terminate()
        try:
            shell.wait(timeout=5)
        except subprocess.TimeoutExpired:
            shell.kill()
            shell.wait(timeout=5)


def _wait_for_plasma(shell: subprocess.Popen[bytes]) -> None:
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        if shell.poll() is not None:
            raise RuntimeError("Plasma Shell exited before publishing its D-Bus API")
        try:
            _evaluate_script("print(desktops().length);")
        except RuntimeError:
            time.sleep(0.2)
            continue
        return
    raise RuntimeError("Plasma Shell did not publish its D-Bus API")


def _configure_script(wallpaper: Path) -> str:
    uri = wallpaper.as_uri()
    return (
        "desktops().forEach(desktop => {"
        'desktop.wallpaperPlugin = "org.kde.image";'
        'desktop.currentConfigGroup = ["Wallpaper", "org.kde.image", "General"];'
        f'desktop.writeConfig("Image", "{uri}");'
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
