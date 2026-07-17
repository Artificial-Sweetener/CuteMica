"""Export the exact native macOS still consumed by CuteMica in CI."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

from PIL import Image
from PySide6.QtWidgets import QApplication

from cutemica.providers.macos_wallpaper import MacOSWallpaperProvider
from cutemica.providers.qt_screens import infer_qt_screen_bindings


def main() -> None:
    """Copy the resolved native still to an explicit artifact path."""

    if len(sys.argv) != 2:
        raise SystemExit("usage: macos_native_source_export.py DESTINATION")
    destination = Path(sys.argv[1])
    application = QApplication([])
    bindings = infer_qt_screen_bindings(application.screens())
    snapshot = MacOSWallpaperProvider().discover(bindings)
    source = snapshot.default_source
    if source.source_kind != "macos-native-still":
        raise RuntimeError(
            f"Expected macos-native-still, received {source.source_kind}"
        )
    with Image.open(source.path) as image:
        image.verify()
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source.path, destination)
    print(f"CUTEMICA_NATIVE_SOURCE_EXPORTED type={source.path.suffix.casefold()}")


if __name__ == "__main__":
    main()
