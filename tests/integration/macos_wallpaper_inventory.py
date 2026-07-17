"""Print native macOS wallpaper state for an ephemeral CI runner."""

from __future__ import annotations

import plistlib
import subprocess
from importlib import import_module
from pathlib import Path
from pprint import pformat
from typing import Any, cast


def main() -> None:
    """Describe AppKit records, WallpaperAgent state, and installed assets."""

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
    store = (
        Path.home()
        / "Library"
        / "Application Support"
        / "com.apple.wallpaper"
        / "Store"
        / "Index.plist"
    )
    print(f"NATIVE STORE exists={store.is_file()}")
    if store.is_file():
        print(pformat(plistlib.loads(store.read_bytes())))


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


if __name__ == "__main__":
    main()
