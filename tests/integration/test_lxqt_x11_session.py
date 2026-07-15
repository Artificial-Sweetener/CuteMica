"""Real-session LXQt wallpaper contract."""

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


def test_lxqt_desktop_session(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    image = wallpaper(tmp_path / "lxqt-session.png")
    environment = desktop_environment("LXQt")
    environment["XDG_CONFIG_HOME"] = str(tmp_path)
    profile = tmp_path / "pcmanfm-qt" / "lxqt" / "settings.conf"
    profile.parent.mkdir(parents=True)
    profile.write_text(
        "\n".join(
            (
                "[Desktop]",
                "WallpaperMode=fit",
                f"Wallpaper={image}",
                "BgColor=#123abc",
                "PerScreenWallpaper=true",
            )
        ),
        encoding="utf-8",
    )
    appearance = tmp_path / "lxqt" / "lxqt.conf"
    appearance.parent.mkdir(parents=True)
    appearance.write_text(
        "[General]\ntheme=dark\n[Qt]\nstyle=Fusion\n", encoding="utf-8"
    )
    (appearance.parent / "session.conf").write_text(
        "[General]\nwindow_manager=openbox\n", encoding="utf-8"
    )
    log_path = tmp_path / "lxqt-session.log"
    desktop = start(("startlxqt",), environment, log_path)
    try:
        wait_for_window_manager(desktop, log_path)
        monkeypatch.setenv("XDG_CURRENT_DESKTOP", "LXQt")
        monkeypatch.setenv("XDG_SESSION_TYPE", "x11")
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))

        snapshot = create_system_wallpaper_provider().discover((binding(),))

        assert snapshot.provider_name == "lxqt"
        assert snapshot.default_source.path == image
        assert snapshot.default_source.placement is WallpaperPlacement.FIT
        assert system_theme(environment) == "Dark"
        run_demo(environment, image)
    finally:
        stop(desktop)
