"""Real-session MATE wallpaper contract."""

import os
import sys
from pathlib import Path

import pytest

from cutemica.enums import WallpaperPlacement
from cutemica.providers.system_wallpaper import create_system_wallpaper_provider
from tests.integration.x11_session import (
    binding,
    desktop_environment,
    run_demo,
    set_gsettings,
    start,
    stop,
    system_theme,
    wait_for_window_manager,
    wallpaper,
)

pytestmark = pytest.mark.skipif(
    sys.platform != "linux"
    or os.environ.get("CUTEMICA_LIGHTWEIGHT_X11_SESSIONS") != "1",
    reason="requires opt-in lightweight X11 desktop sessions",
)


def test_mate_desktop_session(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    image = wallpaper(tmp_path / "mate-session.png")
    environment = desktop_environment("MATE")
    environment.update(
        {
            "DESKTOP_SESSION": "mate",
            "MATE_DESKTOP_SESSION_ID": "this-is-deprecated",
            "XDG_CONFIG_DIRS": "/etc/xdg/xdg-mate:/etc/xdg",
            "XDG_SESSION_DESKTOP": "mate",
        }
    )
    set_gsettings("org.mate.background", "picture-filename", str(image))
    set_gsettings("org.mate.background", "picture-options", "centered")
    set_gsettings("org.mate.background", "primary-color", "#123abc")
    session_log = tmp_path / "mate-session.log"
    session = start(
        ("mate-session", "--disable-acceleration-check"),
        environment,
        session_log,
    )
    try:
        wait_for_window_manager(session, session_log)
        set_gsettings("org.mate.interface", "gtk-theme", "BlackMATE")
        monkeypatch.setenv("XDG_CURRENT_DESKTOP", "MATE")
        monkeypatch.setenv("XDG_SESSION_TYPE", "x11")

        snapshot = create_system_wallpaper_provider().discover((binding(),))

        assert snapshot.provider_name == "mate"
        assert snapshot.default_source.path == image
        assert snapshot.default_source.placement is WallpaperPlacement.CENTER
        assert system_theme(environment) == "Dark"
        run_demo(environment, image)
    finally:
        stop(session)
