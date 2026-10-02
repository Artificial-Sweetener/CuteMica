import os
import shutil
import sys
from pathlib import Path

import pytest

from cutemica.providers import orbit_session

pytestmark = pytest.mark.skipif(
    sys.platform != "linux", reason="requires Linux process/session path semantics"
)


@pytest.fixture
def process_root(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    monkeypatch.setattr(orbit_session, "_PROC_ROOT", tmp_path)
    monkeypatch.setattr(shutil, "which", lambda _: "/bin/appearance")
    monkeypatch.setenv("XDG_CURRENT_DESKTOP", "XFCE")
    monkeypatch.setenv("DISPLAY", ":0.0")
    monkeypatch.delenv("XDG_SESSION_TYPE", raising=False)
    monkeypatch.delenv("WAYLAND_DISPLAY", raising=False)
    return tmp_path


def owner(root: Path, *, name: str = "orbit-desktop", display: str = ":0") -> None:
    process = root / "123"
    process.mkdir()
    (process / "comm").write_text(name + "\n")
    (process / "environ").write_bytes(b"DISPLAY=" + display.encode() + b"\0")


def test_orbit_reader_requires_current_display_owner(process_root: Path) -> None:
    assert orbit_session.orbit_appearance_command() is None
    owner(process_root)
    assert orbit_session.orbit_appearance_command() == "/bin/appearance"


@pytest.mark.parametrize("name,display", [("xfdesktop", ":0"), ("orbit-desktop", ":1")])
def test_other_desktop_or_display_does_not_override(
    process_root: Path, name: str, display: str
) -> None:
    owner(process_root, name=name, display=display)
    assert orbit_session.orbit_appearance_command() is None


def test_other_users_owner_is_ignored(
    process_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    owner(process_root)
    uid = os.getuid()
    monkeypatch.setattr(os, "getuid", lambda: uid + 1)
    assert orbit_session.orbit_appearance_command() is None


def test_unreadable_owner_metadata_is_ignored(process_root: Path) -> None:
    owner(process_root)
    (process_root / "123" / "environ").unlink()
    assert orbit_session.orbit_appearance_command() is None


def test_explicit_orbit_session_requires_installed_reader(
    process_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("XDG_CURRENT_DESKTOP", "Orbit:XFCE")
    assert orbit_session.orbit_appearance_command() == "/bin/appearance"
    monkeypatch.setattr(shutil, "which", lambda _: None)
    assert orbit_session.orbit_appearance_command() is None


def test_wayland_owner_matches_wayland_session(
    process_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    owner(process_root)
    monkeypatch.setenv("WAYLAND_DISPLAY", "wayland-1")
    monkeypatch.setenv("XDG_RUNTIME_DIR", "/run/user/1000")
    assert orbit_session.orbit_appearance_command() is None
    (process_root / "123" / "environ").write_bytes(
        b"WAYLAND_DISPLAY=wayland-1\0XDG_RUNTIME_DIR=/run/user/1000\0"
    )
    assert orbit_session.orbit_appearance_command() == "/bin/appearance"


def test_x11_session_ignores_inherited_wayland_owner(
    process_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    owner(process_root, display=":1")
    monkeypatch.setenv("XDG_SESSION_TYPE", "x11")
    monkeypatch.setenv("WAYLAND_DISPLAY", "wayland-0")
    monkeypatch.setenv("XDG_RUNTIME_DIR", "/run/user/1000")
    (process_root / "123" / "environ").write_bytes(
        b"DISPLAY=:1\0WAYLAND_DISPLAY=wayland-0\0XDG_RUNTIME_DIR=/run/user/1000\0"
    )
    assert orbit_session.orbit_appearance_command() is None


def test_same_wayland_name_in_other_runtime_directory_is_not_owner(
    process_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    owner(process_root)
    monkeypatch.setenv("XDG_SESSION_TYPE", "wayland")
    monkeypatch.setenv("WAYLAND_DISPLAY", "wayland-0")
    monkeypatch.setenv("XDG_RUNTIME_DIR", "/run/user/1000/nested")
    (process_root / "123" / "environ").write_bytes(
        b"WAYLAND_DISPLAY=wayland-0\0XDG_RUNTIME_DIR=/run/user/1000\0"
    )
    assert orbit_session.orbit_appearance_command() is None
