from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication, QMessageBox

from cutemica.controller import MaterialController
from cutemica.demo.smoke import DemoSmokeSequence
from cutemica.demo.window import DemoWindow
from cutemica.diagnostics.runtime_exceptions import install_exception_recorder
from cutemica.diagnostics.session import ValidationSession
from cutemica.diagnostics.startup_failure import write_startup_failure
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
    application.setApplicationDisplayName("CuteMica Tester")
    application.setOrganizationName("CuteMica")

    try:
        return _run(application, arguments)
    except Exception as error:  # noqa: BLE001 - desktop application boundary
        report_path = write_startup_failure(error)
        QMessageBox.critical(
            None,
            "CuteMica could not start",
            "CuteMica could not read the desktop configuration.\n\n"
            f"A diagnostic report was saved to Downloads:\n{report_path.name}",
        )
        return 1


def _run(application: QApplication, arguments: argparse.Namespace) -> int:
    bindings = infer_qt_screen_bindings(application.screens())
    wallpaper_provider = (
        ExplicitWallpaperProvider(arguments.wallpaper)
        if arguments.wallpaper is not None
        else create_system_wallpaper_provider()
    )
    wallpaper = wallpaper_provider.discover(bindings)
    theme = ThemeController(ThemeMode(arguments.theme))
    controller = MaterialController(wallpaper, bindings, theme)
    session = ValidationSession(bindings, theme.resolved, wallpaper.provider_name)
    install_exception_recorder(session)
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
        session,
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


def _parse_arguments(arguments: list[str] | None = None) -> argparse.Namespace:
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
    command_line = sys.argv[1:] if arguments is None else arguments
    finder_safe_arguments = [
        argument for argument in command_line if not argument.startswith("-psn_")
    ]
    parsed = parser.parse_args(finder_safe_arguments)
    if (parsed.width is None) != (parsed.height is None):
        parser.error("--width and --height must be provided together")
    if (parsed.x is None) != (parsed.y is None):
        parser.error("--x and --y must be provided together")
    if parsed.width is not None and parsed.width <= 0:
        parser.error("--width must be positive")
    if parsed.height is not None and parsed.height <= 0:
        parser.error("--height must be positive")
    return parsed


if __name__ == "__main__":
    raise SystemExit(main())
