"""Activate and verify Apple's installed native animated wallpaper mode."""

from __future__ import annotations

import plistlib
import subprocess
import time
from importlib import import_module
from pathlib import Path
from typing import Any, cast


def main() -> None:
    """Replace hosted-runner static choices and verify the native mode."""

    activate_system_default()
    assert_native_mode()


def activate_system_default() -> None:
    """Select WallpaperAgent's native default in every desktop scope."""

    store = wallpaper_store_path()
    state = plistlib.loads(store.read_bytes())
    replacements = _replace_desktop_choices(state)
    if not replacements:
        raise RuntimeError("Native wallpaper store had no desktop choices")
    store.write_bytes(plistlib.dumps(state, fmt=plistlib.FMT_BINARY))
    print(f"Activated native desktop choices: {replacements}")
    subprocess.run(["killall", "WallpaperAgent"], check=False)
    time.sleep(12)


def assert_native_mode() -> None:
    """Fail unless AppKit exposes the installed MOV-backed default still."""

    appkit: Any = import_module("AppKit")
    foundation: Any = import_module("Foundation")
    defaults: Any = foundation.NSUserDefaults.standardUserDefaults()
    domain = cast(
        dict[str, Any] | None,
        defaults.persistentDomainForName_("com.apple.wallpaper"),
    )
    system_url = domain.get("SystemWallpaperURL") if domain else None
    if not isinstance(system_url, str) or not system_url.casefold().endswith(".mov"):
        raise RuntimeError("WallpaperAgent did not expose a native MOV wallpaper")
    workspace: Any = appkit.NSWorkspace.sharedWorkspace()
    screens = cast(list[Any], appkit.NSScreen.screens())
    if not screens:
        raise RuntimeError("AppKit did not expose a screen")
    suffixes: list[str] = []
    for screen in screens:
        url: Any = workspace.desktopImageURLForScreen_(screen)
        if url is None:
            raise RuntimeError("AppKit did not expose a desktop image URL")
        suffixes.append(Path(cast(str, url.path())).suffix.casefold())
    if any(suffix != ".heic" for suffix in suffixes):
        raise RuntimeError("AppKit did not expose the native wallpaper HEIC still")
    print(f"CUTEMICA_MACOS_NATIVE_MODE_OK screens={len(screens)}")


def wallpaper_store_path() -> Path:
    """Return WallpaperAgent's per-user store path."""

    return (
        Path.home()
        / "Library"
        / "Application Support"
        / "com.apple.wallpaper"
        / "Store"
        / "Index.plist"
    )


def _replace_desktop_choices(value: object) -> int:
    replacements = 0
    if isinstance(value, dict):
        for key, child in value.items():
            if key == "Desktop" and isinstance(child, dict):
                content = child.get("Content")
                if isinstance(content, dict):
                    content["Choices"] = [
                        {"Configuration": b"", "Files": [], "Provider": "default"}
                    ]
                    content["Shuffle"] = "$null"
                    replacements += 1
            replacements += _replace_desktop_choices(child)
    elif isinstance(value, list):
        replacements += sum(_replace_desktop_choices(child) for child in value)
    return replacements


if __name__ == "__main__":
    main()
