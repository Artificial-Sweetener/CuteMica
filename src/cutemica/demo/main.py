from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from cutemica.controller import MaterialController
from cutemica.demo.smoke import DemoSmokeSequence
from cutemica.demo.window import DemoWindow
from cutemica.enums import ThemeMode
from cutemica.providers.explicit_wallpaper import ExplicitWallpaperProvider
from cutemica.providers.qt_screens import infer_qt_screen_bindings
from cutemica.providers.system_wallpaper import create_system_wallpaper_provider
from cutemica.providers.wallpaper_monitor import WallpaperMonitor
from cutemica.providers.window_geometry import create_window_geometry_provider
from cutemica.theme import ThemeController


def main() -> int:
    arguments = _parse_arguments()
    application = QApplication(sys.argv)
    application.setApplicationName("CuteMica")
    application.setOrganizationName("CuteMica")

    bindings = infer_qt_screen_bindings(application.screens())
    wallpaper_provider = (
        ExplicitWallpaperProvider(arguments.wallpaper)
        if arguments.wallpaper is not None
        else create_system_wallpaper_provider()
    )
    wallpaper = wallpaper_provider.discover(bindings)
    theme = ThemeController(ThemeMode(arguments.theme))
    controller = MaterialController(wallpaper, bindings, theme)
    monitor = WallpaperMonitor(
        wallpaper_provider,
        bindings,
        wallpaper,
        parent=controller,
    )
    monitor.snapshot_changed.connect(controller.set_wallpaper)
    monitor.failed.connect(controller.error)
    window = DemoWindow(
        controller,
        theme,
        wallpaper,
        create_window_geometry_provider(bindings),
    )
    if arguments.width is not None and arguments.height is not None:
        window.resize(arguments.width, arguments.height)
    if arguments.x is not None and arguments.y is not None:
        window.move(arguments.x, arguments.y)
    window.show()
    monitor.start()

    sequence: DemoSmokeSequence | None = None
    if arguments.smoke_test or arguments.screenshot is not None:
        sequence = DemoSmokeSequence(
            application,
            window,
            theme,
            controller,
            screenshot_path=arguments.screenshot,
            exercise_theme_change=arguments.smoke_test,
        )
        sequence.start()
    exit_code = application.exec()
    if sequence is not None and sequence.error is not None:
        print(sequence.error, file=sys.stderr)
    if arguments.smoke_test and exit_code == 0:
        print("CUTEMICA_SMOKE_OK")
    return exit_code


def _parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Launch the CuteMica demo")
    parser.add_argument(
        "--wallpaper",
        type=Path,
        help="Wallpaper image; required where automatic discovery is unavailable",
    )
    parser.add_argument(
        "--theme",
        choices=tuple(mode.value for mode in ThemeMode),
        default=ThemeMode.AUTO.value,
        help="Theme mode for the material",
    )
    parser.add_argument("--x", type=int, help="Window left edge in Qt DIPs")
    parser.add_argument("--y", type=int, help="Window top edge in Qt DIPs")
    parser.add_argument("--width", type=int, help="Window width in Qt DIPs")
    parser.add_argument("--height", type=int, help="Window height in Qt DIPs")
    parser.add_argument(
        "--smoke-test",
        action="store_true",
        help="Exercise generation and a theme change, then exit",
    )
    parser.add_argument(
        "--screenshot",
        type=Path,
        help="Save a Qt-rendered demo screenshot, then exit",
    )
    arguments = parser.parse_args()
    if (arguments.width is None) != (arguments.height is None):
        parser.error("--width and --height must be provided together")
    if (arguments.x is None) != (arguments.y is None):
        parser.error("--x and --y must be provided together")
    if arguments.width is not None and arguments.width <= 0:
        parser.error("--width must be positive")
    if arguments.height is not None and arguments.height <= 0:
        parser.error("--height must be positive")
    return arguments


if __name__ == "__main__":
    raise SystemExit(main())
