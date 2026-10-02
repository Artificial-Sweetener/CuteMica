import json
from pathlib import Path

import pytest
from PIL import Image

from cutemica.geometry import Rect, ScreenBinding
from cutemica.providers.gnome_wallpaper import GnomeWallpaperProvider
from cutemica.providers.mate_wallpaper import MateWallpaperProvider
from cutemica.providers.plasma_wallpaper import PlasmaWallpaperProvider


@pytest.mark.parametrize("as_uri", [False, True])
@pytest.mark.parametrize("desktop", ["gnome", "plasma"])
def test_percent_filename_keeps_its_literal_characters(
    tmp_path: Path, as_uri: bool, desktop: str
) -> None:
    path = tmp_path / "winter %20 # 雪.png"
    Image.new("RGB", (8, 8)).save(path, format="PNG")
    value = path.as_uri() if as_uri else str(path)
    if desktop == "gnome":
        values = {
            "color-scheme": "'default'",
            "picture-uri": repr(value),
            "picture-options": "'zoom'",
            "primary-color": "'#000000'",
        }
        snapshot = GnomeWallpaperProvider(lambda args: values[args[3]]).discover(())
    else:
        record = [
            {
                "screen": 0,
                "plugin": "org.kde.image",
                "image": value,
                "fillMode": 2,
                "color": "#000000",
            }
        ]
        rect = Rect(0, 0, 100, 100)
        binding = ScreenBinding("one", rect, "one", rect, 1.0)
        snapshot = PlasmaWallpaperProvider(lambda _: json.dumps(record)).discover(
            (binding,)
        )
    assert snapshot.default_source.path == path


@pytest.mark.parametrize("desktop", ["gnome", "mate"])
def test_color_only_desktop_does_not_publish_unused_image(
    tmp_path: Path, desktop: str
) -> None:
    path = tmp_path / "configured-but-disabled.png"
    Image.new("RGB", (8, 8)).save(path, format="PNG")
    values = {
        "color-scheme": "'default'",
        "picture-uri": repr(path.as_uri()),
        "picture-filename": repr(str(path)),
        "picture-options": "'none'",
        "primary-color": "'#123456'",
    }
    with pytest.raises(RuntimeError, match="color without an image"):
        if desktop == "gnome":
            GnomeWallpaperProvider(lambda args: values[args[3]]).discover(())
        else:
            MateWallpaperProvider(lambda args: values[args[3]]).discover(())


def test_localhost_file_uri_remains_supported(tmp_path: Path) -> None:
    from cutemica.providers.wallpaper_values import path_from_uri

    path = tmp_path / "literal %25 # snow.png"
    uri = path.as_uri().replace("file:///", "file://localhost/", 1)
    assert path_from_uri(uri, "Linux desktop") == path


@pytest.mark.parametrize("desktop", ["gnome", "plasma"])
def test_remote_file_uri_does_not_select_an_existing_local_file(
    tmp_path: Path, desktop: str
) -> None:
    path = tmp_path / "local.png"
    Image.new("RGB", (8, 8)).save(path, format="PNG")
    uri = path.as_uri().replace("file:///", "file://remote/", 1)
    with pytest.raises(RuntimeError, match="remote host"):
        if desktop == "gnome":
            values = {
                "color-scheme": "'default'",
                "picture-uri": repr(uri),
                "picture-options": "'zoom'",
                "primary-color": "'#000000'",
            }
            GnomeWallpaperProvider(lambda args: values[args[3]]).discover(())
        else:
            records = [
                {
                    "screen": 0,
                    "plugin": "org.kde.image",
                    "image": uri,
                    "fillMode": 2,
                    "color": "#000000",
                }
            ]
            rect = Rect(0, 0, 100, 100)
            binding = ScreenBinding("one", rect, "one", rect, 1.0)
            PlasmaWallpaperProvider(lambda _: json.dumps(records)).discover((binding,))


@pytest.mark.parametrize("as_uri", [False, True])
def test_plasma_does_not_interpret_literal_filename_as_gvariant(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, as_uri: bool
) -> None:
    monkeypatch.chdir(tmp_path)
    path = Path("'quoted-wallpaper.png'")
    Image.new("RGB", (8, 8)).save(path, format="PNG")
    value = path.resolve().as_uri().replace("%27", "'") if as_uri else str(path)
    records = [
        {
            "screen": 0,
            "plugin": "org.kde.image",
            "image": value,
            "fillMode": 2,
            "color": "#000000",
        }
    ]
    rect = Rect(0, 0, 100, 100)
    binding = ScreenBinding("one", rect, "one", rect, 1.0)
    snapshot = PlasmaWallpaperProvider(lambda _: json.dumps(records)).discover(
        (binding,)
    )
    assert snapshot.default_source.path == (path.resolve() if as_uri else path)
