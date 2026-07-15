"""Shared lifecycle operations for isolated X11 desktop tests."""

from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

from PIL import Image

from cutemica.geometry import Rect, ScreenBinding


def wallpaper(path: Path) -> Path:
    Image.new("RGB", (16, 9), (40, 80, 120)).save(path)
    return path


def binding() -> ScreenBinding:
    geometry = Rect(0, 0, 1920, 1080)
    return ScreenBinding("virtual", geometry, "Virtual-1", geometry, 1.0)


def desktop_environment(desktop: str) -> dict[str, str]:
    environment = os.environ.copy()
    environment.pop("WAYLAND_DISPLAY", None)
    environment.update(
        {
            "CLUTTER_BACKEND": "x11",
            "GDK_BACKEND": "x11",
            "QT_QPA_PLATFORM": "xcb",
            "XDG_CURRENT_DESKTOP": desktop,
            "XDG_SESSION_TYPE": "x11",
        }
    )
    return environment


def set_gsettings(schema: str, key: str, value: str) -> None:
    subprocess.run(
        ("gsettings", "set", schema, key, repr(value)),
        check=True,
        capture_output=True,
        text=True,
        timeout=10,
    )


def set_xfconf(
    property_name: str,
    value_type: str,
    value: str,
    *,
    channel: str = "xfce4-desktop",
) -> None:
    subprocess.run(
        (
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
        ),
        check=True,
        capture_output=True,
        text=True,
        timeout=10,
    )


def start(
    arguments: tuple[str, ...],
    environment: dict[str, str],
    log_path: Path,
) -> subprocess.Popen[bytes]:
    log = log_path.open("wb", buffering=0)
    process = subprocess.Popen(
        arguments,
        env=environment,
        stdout=log,
        stderr=subprocess.STDOUT,
    )
    log.close()
    return process


def wait_for_process(process: subprocess.Popen[bytes], log_path: Path) -> None:
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(f"Desktop process exited:\n{log_tail(log_path)}")
        time.sleep(0.2)
    if process.poll() is not None:
        raise RuntimeError(f"Desktop process exited:\n{log_tail(log_path)}")


def wait_for_window_manager(
    process: subprocess.Popen[bytes],
    log_path: Path,
) -> None:
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(f"Window manager exited:\n{log_tail(log_path)}")
        completed = subprocess.run(
            ("xprop", "-root", "_NET_SUPPORTING_WM_CHECK"),
            capture_output=True,
            text=True,
            timeout=5,
        )
        if "window id" in completed.stdout.casefold():
            return
        time.sleep(0.2)
    raise RuntimeError("Window manager did not become ready")


def run_demo(environment: dict[str, str], wallpaper_path: Path) -> None:
    completed = subprocess.run(
        (
            sys.executable,
            "-m",
            "cutemica.demo.main",
            "--wallpaper",
            str(wallpaper_path),
            "--smoke-test",
        ),
        env=environment,
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    )
    if "CUTEMICA_SMOKE_OK" not in completed.stdout:
        raise RuntimeError("CuteMica demo did not report a successful smoke test")


def system_theme(environment: dict[str, str]) -> str:
    completed = subprocess.run(
        (sys.executable, str(Path(__file__).with_name("system_theme_probe.py"))),
        env=environment,
        check=True,
        capture_output=True,
        text=True,
        timeout=10,
    )
    return completed.stdout.strip()


def log_tail(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")[-4_000:]
    except OSError:
        return "log unavailable"


def stop(process: subprocess.Popen[bytes]) -> None:
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)
