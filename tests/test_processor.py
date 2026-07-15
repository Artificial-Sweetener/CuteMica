from PIL import Image

from cutemica.core.processor import process_mica_alt
from cutemica.recipe import ResolvedMicaAltStyle


def test_full_tint_opacity_produces_the_material_color() -> None:
    style = ResolvedMicaAltStyle(
        material_color=(20, 30, 40),
        tint_opacity=1.0,
        luminosity_opacity=1.0,
        blur_radius_dip=64,
        fallback_color=(0, 0, 0),
    )

    result = process_mica_alt(Image.new("RGB", (20, 20), "red"), style, 0.25)

    assert result.getpixel((10, 10)) == (20, 30, 40)


def test_luminosity_layer_maps_neutral_wallpaper_to_material_luminosity() -> None:
    style = ResolvedMicaAltStyle(
        material_color=(218, 218, 218),
        tint_opacity=0.5,
        luminosity_opacity=1.0,
        blur_radius_dip=0,
        fallback_color=(232, 232, 232),
    )

    result = process_mica_alt(Image.new("RGB", (8, 8), (9, 9, 9)), style, 0.25)

    assert result.getpixel((4, 4)) == (218, 218, 218)
