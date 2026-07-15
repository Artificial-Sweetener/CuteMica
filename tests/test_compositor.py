import pytest
from PIL import Image

from cutemica.core.compositor import compose_wallpaper
from cutemica.enums import WallpaperPlacement
from cutemica.geometry import Rect, ScreenBinding


def binding(identifier: str, x: int) -> ScreenBinding:
    geometry = Rect(x, 0, 100, 100)
    return ScreenBinding(identifier, geometry, identifier, geometry, 1.0)


@pytest.mark.parametrize("placement", list(WallpaperPlacement))
def test_every_placement_produces_the_requested_material_size(
    placement: WallpaperPlacement,
) -> None:
    screen = binding("primary", 0)
    wallpaper = Image.new("RGB", (160, 90), (80, 120, 200))

    result = compose_wallpaper(wallpaper, placement, screen, (screen,), 0.5)

    assert result.size == (50, 50)


def test_span_uses_virtual_desktop_coordinates() -> None:
    wallpaper = Image.new("RGB", (200, 100), "red")
    wallpaper.paste(Image.new("RGB", (100, 100), "blue"), (100, 0))
    left = binding("left", 0)
    right = binding("right", 100)

    left_result = compose_wallpaper(
        wallpaper, WallpaperPlacement.SPAN, left, (left, right), 1.0
    )
    right_result = compose_wallpaper(
        wallpaper, WallpaperPlacement.SPAN, right, (left, right), 1.0
    )

    left_pixel = left_result.getpixel((50, 50))
    right_pixel = right_result.getpixel((50, 50))
    assert isinstance(left_pixel, tuple)
    assert isinstance(right_pixel, tuple)
    assert left_pixel[0] > 240
    assert right_pixel[2] > 240


def test_material_size_is_a_fraction_of_native_physical_geometry() -> None:
    screen = ScreenBinding(
        "portrait",
        Rect(0, 0, 150, 300),
        "portrait",
        Rect(0, 0, 100, 200),
        1.5,
    )

    result = compose_wallpaper(
        Image.new("RGB", (150, 300)),
        WallpaperPlacement.FILL,
        screen,
        (screen,),
        0.5,
    )

    assert result.size == (75, 150)


def test_invalid_texture_scale_fails_fast() -> None:
    screen = binding("primary", 0)
    with pytest.raises(ValueError, match="Texture scale"):
        compose_wallpaper(
            Image.new("RGB", (10, 10)),
            WallpaperPlacement.FILL,
            screen,
            (screen,),
            0,
        )
