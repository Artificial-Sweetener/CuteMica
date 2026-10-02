import json
import sys
import traceback
from pathlib import Path

import pytest
from PIL import Image

from cutemica.enums import WallpaperPlacement
from cutemica.providers import system_wallpaper


def test_orbit_owner_overrides_xfce_advertisement(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from cutemica.providers import orbit_session

    monkeypatch.setattr(sys, "platform", "linux")
    monkeypatch.setenv("XDG_CURRENT_DESKTOP", "XFCE")
    monkeypatch.setattr(orbit_session, "orbit_appearance_command", lambda: "/bin/orbit")
    provider = system_wallpaper.create_system_wallpaper_provider()
    assert provider.name == "orbit"


def test_orbit_reads_literal_path_and_observes_wallpaper_changes(
    tmp_path: Path,
) -> None:
    from cutemica.providers.orbit_wallpaper import OrbitWallpaperProvider

    first = tmp_path / "wallpaper %20 # 雪.png"
    second = tmp_path / "second.png"
    for path in (first, second):
        Image.new("RGB", (8, 8)).save(path)
    responses = iter((first, second))
    commands: list[tuple[str, ...]] = []

    def run(arguments: tuple[str, ...]) -> str:
        commands.append(arguments)
        return json.dumps({"wallpaper": str(next(responses)), "accent": "#ff8066"})

    provider = OrbitWallpaperProvider("/bin/appearance", runner=run)
    first_snapshot = provider.discover(())
    second_snapshot = provider.discover(())

    assert first_snapshot.provider_name == "orbit"
    assert first_snapshot.default_source.path == first
    assert first_snapshot.default_source.placement is WallpaperPlacement.FILL
    assert second_snapshot.default_source.path == second
    assert commands == [("/bin/appearance", "read")] * 2
    assert provider.capabilities.automatic_wallpaper
    assert provider.capabilities.wallpaper_changes
    assert not provider.capabilities.per_screen_wallpaper
    assert not provider.requires_main_thread


@pytest.mark.parametrize(
    "value", ["invalid", "[]", "{}", '{"wallpaper":3}', '{"wallpaper":"relative.png"}']
)
def test_orbit_rejects_invalid_metadata(value: str) -> None:
    from cutemica.providers.orbit_wallpaper import OrbitWallpaperProvider

    provider = OrbitWallpaperProvider("/bin/appearance", runner=lambda _: value)
    with pytest.raises(RuntimeError, match="Orbit"):
        provider.discover(())


def test_missing_orbit_source_does_not_disclose_path(tmp_path: Path) -> None:
    from cutemica.providers.orbit_wallpaper import OrbitWallpaperProvider

    path = tmp_path / "private-photo.png"
    provider = OrbitWallpaperProvider(
        "/bin/appearance", runner=lambda _: json.dumps({"wallpaper": str(path)})
    )
    with pytest.raises(RuntimeError, match="unavailable") as caught:
        provider.discover(())
    assert str(path) not in "".join(traceback.format_exception(caught.value))


def test_orbit_command_failures_are_bounded_and_redacted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import subprocess

    from cutemica.providers import orbit_wallpaper

    def fail(
        arguments: tuple[str, ...],
        *,
        check: bool,
        capture_output: bool,
        text: bool,
        timeout: int,
    ) -> subprocess.CompletedProcess[str]:
        assert arguments == ("/bin/appearance", "read")
        assert check and capture_output and text and timeout == 5
        raise subprocess.TimeoutExpired(arguments, timeout, output="private-path")

    monkeypatch.setattr(subprocess, "run", fail)
    with pytest.raises(RuntimeError, match="Could not read Orbit") as caught:
        orbit_wallpaper.OrbitWallpaperProvider("/bin/appearance").discover(())
    assert "private-path" not in str(caught.value)


@pytest.mark.parametrize(
    "desktop,name",
    [
        ("GNOME", "gnome"),
        ("KDE", "kde-plasma"),
        ("MATE", "mate"),
        ("XFCE", "xfce"),
        ("LXQt", "lxqt"),
    ],
)
def test_without_orbit_owner_native_linux_dispatch_is_preserved(
    monkeypatch: pytest.MonkeyPatch,
    desktop: str,
    name: str,
) -> None:
    from cutemica.providers import orbit_session

    monkeypatch.setattr(sys, "platform", "linux")
    monkeypatch.setenv("XDG_CURRENT_DESKTOP", desktop)
    monkeypatch.setattr(orbit_session, "orbit_appearance_command", lambda: None)
    assert system_wallpaper.create_system_wallpaper_provider().name == name


@pytest.mark.parametrize(
    "platform,name", [("win32", "windows-desktop-api"), ("darwin", "macos-appkit")]
)
def test_non_linux_platform_does_not_probe_orbit(
    monkeypatch: pytest.MonkeyPatch,
    platform: str,
    name: str,
) -> None:
    from cutemica.providers import orbit_session

    def unexpected() -> None:
        raise AssertionError("Non-Linux selection queried Orbit")

    monkeypatch.setattr(sys, "platform", platform)
    monkeypatch.setattr(orbit_session, "orbit_appearance_command", unexpected)
    assert system_wallpaper.create_system_wallpaper_provider().name == name
