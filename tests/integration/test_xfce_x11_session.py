"""Real-session XFCE wallpaper contract."""

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
    set_xfconf,
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


def test_xfce_desktop_session(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    image = wallpaper(tmp_path / "xfce-session.png")
    environment = desktop_environment("XFCE")
    base = "/backdrop/screen0/monitorVirtual-1/workspace0"
    set_xfconf(f"{base}/last-image", "string", str(image))
    set_xfconf(f"{base}/image-style", "int", "5")
    set_xfconf("/Net/ThemeName", "string", "Adwaita-dark", channel="xsettings")
    log_path = tmp_path / "xfce4-session.log"
    session = start(("xfce4-session",), environment, log_path)
    try:
        wait_for_window_manager(session, log_path)
        monkeypatch.setenv("XDG_CURRENT_DESKTOP", "XFCE")
        monkeypatch.setenv("XDG_SESSION_TYPE", "x11")

        snapshot = create_system_wallpaper_provider().discover((binding(),))

        assert snapshot.provider_name == "xfce"
        assert snapshot.default_source.path == image
        assert snapshot.default_source.placement is WallpaperPlacement.FILL
        assert system_theme(environment) == "Dark"
        run_demo(environment, image)
    finally:
        stop(session)
