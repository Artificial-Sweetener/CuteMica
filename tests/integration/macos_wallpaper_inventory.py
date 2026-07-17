"""Print native macOS wallpaper state for an ephemeral CI runner."""

from __future__ import annotations

import argparse
import plistlib
import subprocess
import time
from importlib import import_module
from pathlib import Path
from pprint import pformat
from typing import Any, cast


def main() -> None:
    """Describe AppKit records, WallpaperAgent state, and installed assets."""

    arguments = _parse_arguments()
    if arguments.activate_system_default:
        _activate_system_default()
    print(_command("sw_vers"))
    _print_appkit_records()
    _print_wallpaper_processes()
    _print_domain()
    _print_store()
    for root in _asset_roots():
        _print_inventory(root)


def _print_appkit_records() -> None:
    appkit: Any = import_module("AppKit")
    workspace: Any = appkit.NSWorkspace.sharedWorkspace()
    screens = cast(list[Any], appkit.NSScreen.screens())
    for index, screen in enumerate(screens):
        url: Any = workspace.desktopImageURLForScreen_(screen)
        options = cast(
            dict[Any, Any], workspace.desktopImageOptionsForScreen_(screen) or {}
        )
        path = Path(cast(str, url.path())) if url is not None else None
        image: Any = (
            appkit.NSImage.alloc().initWithContentsOfURL_(url)
            if url is not None
            else None
        )
        print(f"APPKIT SCREEN {index}")
        print(f"url={url.absoluteString() if url is not None else None}")
        print(f"scheme={url.scheme() if url is not None else None}")
        print(f"path_exists={path.exists() if path is not None else None}")
        print(f"path_is_file={path.is_file() if path is not None else None}")
        print(f"suffix={path.suffix if path is not None else None}")
        print(f"options={pformat(dict(options))}")
        print(f"nsimage_decodable={image is not None}")
        if image is not None:
            size: Any = image.size()
            print(f"nsimage_size={size.width}x{size.height}")


def _print_wallpaper_processes() -> None:
    process_table = _command("ps", "-axo", "pid,command")
    matching = (
        line
        for line in process_table.splitlines()
        if any(word in line.casefold() for word in ("wallpaper", "idleasset", "aerial"))
    )
    print("WALLPAPER PROCESSES")
    print("\n".join(matching))


def _print_domain() -> None:
    completed = subprocess.run(
        ["defaults", "export", "com.apple.wallpaper", "-"],
        check=False,
        capture_output=True,
    )
    print("COM.APPLE.WALLPAPER DOMAIN")
    if completed.returncode:
        print(completed.stderr.decode(errors="replace"))
        return
    print(pformat(plistlib.loads(completed.stdout)))


def _print_store() -> None:
    store = _store_path()
    print(f"NATIVE STORE exists={store.is_file()}")
    if store.is_file():
        print(pformat(plistlib.loads(store.read_bytes())))


def _activate_system_default() -> None:
    store = _store_path()
    state = plistlib.loads(store.read_bytes())
    replacements = _replace_desktop_choices(state)
    if not replacements:
        raise RuntimeError("Native wallpaper store had no desktop choices")
    store.write_bytes(plistlib.dumps(state, fmt=plistlib.FMT_BINARY))
    print(f"REPLACED DESKTOP CHOICES count={replacements}")
    subprocess.run(["killall", "WallpaperAgent"], check=False)
    time.sleep(12)


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


def _store_path() -> Path:
    return (
        Path.home()
        / "Library"
        / "Application Support"
        / "com.apple.wallpaper"
        / "Store"
        / "Index.plist"
    )


def _asset_roots() -> tuple[Path, ...]:
    return (
        Path("/System/Library/Desktop Pictures"),
        Path("/Library/Application Support/com.apple.idleassetsd"),
        Path.home() / "Library/Application Support/com.apple.wallpaper",
        Path("/Library/Caches/Desktop Pictures"),
        Path.home() / "Library/Caches/com.apple.wallpaper",
    )


def _print_inventory(root: Path) -> None:
    print(f"ASSET ROOT {root} exists={root.is_dir()}")
    if not root.is_dir():
        return
    try:
        files = sorted(path for path in root.rglob("*") if path.is_file())[:200]
    except OSError as error:
        print(f"inventory_error={error}")
        return
    for path in files:
        try:
            relative = path.relative_to(root)
            size = path.stat().st_size
        except OSError as error:
            print(f"entry_error={error}")
            continue
        print(f"asset={relative} bytes={size}")


def _command(*arguments: str) -> str:
    return subprocess.run(
        list(arguments),
        check=False,
        capture_output=True,
        text=True,
    ).stdout


def _parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--activate-system-default", action="store_true")
    return parser.parse_args()


if __name__ == "__main__":
    main()
