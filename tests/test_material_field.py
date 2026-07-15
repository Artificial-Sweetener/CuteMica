import numpy as np
from PIL import Image

from cutemica.core.blur_plan import resolve_blur_plan
from cutemica.core.compositor import compose_wallpaper
from cutemica.core.material_field import PreparedMaterialField, prepare_material_field
from cutemica.core.processor import process_mica_alt
from cutemica.enums import ResolvedTheme, WallpaperPlacement
from cutemica.geometry import Rect, ScreenBinding
from cutemica.recipe import MicaAltRecipe


def mixed_density_screens() -> tuple[ScreenBinding, ScreenBinding]:
    high_density = ScreenBinding(
        "high-density",
        Rect(0, 0, 800, 400),
        "high-density",
        Rect(0, 0, 533, 267),
        1.5,
    )
    standard = ScreenBinding(
        "standard",
        Rect(800, 0, 800, 400),
        "standard",
        Rect(800, 0, 800, 400),
        1.0,
    )
    return high_density, standard


def test_neighbor_halo_is_bounded_to_the_shared_screen_sides() -> None:
    screens = mixed_density_screens()
    wallpaper = split_wallpaper()
    recipe = MicaAltRecipe()
    high_density, standard = screens
    high_scale = recipe.texture_scale_for(high_density.device_pixel_ratio)
    standard_scale = recipe.texture_scale_for(standard.device_pixel_ratio)

    high_field = _prepared_field(wallpaper, high_density, screens, recipe)
    standard_field = _prepared_field(wallpaper, standard, screens, recipe)

    assert high_field.image.size == (round(800 * high_scale) + 258, 200)
    assert high_field.material_box == (0, 0, 400, 200)
    assert standard_field.image.size == (round(800 * standard_scale) + 81, 100)
    assert standard_field.material_box == (81, 0, 281, 100)


def test_neighbor_halo_smooths_seam_without_changing_distant_material() -> None:
    screens = mixed_density_screens()
    wallpaper = split_wallpaper()
    recipe = MicaAltRecipe()
    legacy = [
        _processed(wallpaper, screen, screens, recipe, False) for screen in screens
    ]
    joined = [
        _processed(wallpaper, screen, screens, recipe, True) for screen in screens
    ]

    legacy_delta = np.abs(legacy[0][100, -1] - legacy[1][50, 0])
    joined_delta = np.abs(joined[0][100, -1] - joined[1][50, 0])

    assert int(joined_delta.max()) < int(legacy_delta.max()) / 2
    np.testing.assert_array_equal(joined[0][:, :100], legacy[0][:, :100])
    np.testing.assert_array_equal(joined[1][:, 100:], legacy[1][:, 100:])


def split_wallpaper() -> Image.Image:
    wallpaper = Image.new("RGB", (1600, 400), (0, 10, 40))
    wallpaper.paste(Image.new("RGB", (800, 400), (80, 0, 80)), (800, 0))
    return wallpaper


def _prepared_field(
    wallpaper: Image.Image,
    screen: ScreenBinding,
    screens: tuple[ScreenBinding, ScreenBinding],
    recipe: MicaAltRecipe,
) -> PreparedMaterialField:
    scale = recipe.texture_scale_for(screen.device_pixel_ratio)
    style = recipe.resolve(ResolvedTheme.DARK, screen.device_pixel_ratio)
    pixels_per_dip = screen.texture_pixels_per_dip(scale)
    return prepare_material_field(
        wallpaper,
        WallpaperPlacement.SPAN,
        screen,
        screens,
        scale,
        resolve_blur_plan(style, pixels_per_dip),
    )


def _processed(
    wallpaper: Image.Image,
    screen: ScreenBinding,
    screens: tuple[ScreenBinding, ScreenBinding],
    recipe: MicaAltRecipe,
    neighbor_aware: bool,
) -> np.ndarray:
    scale = recipe.texture_scale_for(screen.device_pixel_ratio)
    style = recipe.resolve(ResolvedTheme.DARK, screen.device_pixel_ratio)
    pixels_per_dip = screen.texture_pixels_per_dip(scale)
    if neighbor_aware:
        prepared = _prepared_field(wallpaper, screen, screens, recipe)
        processed = process_mica_alt(prepared.image, style, pixels_per_dip)
        result = processed.crop(prepared.material_box)
    else:
        field = compose_wallpaper(
            wallpaper,
            WallpaperPlacement.SPAN,
            screen,
            screens,
            scale,
        )
        result = process_mica_alt(field, style, pixels_per_dip)
    return np.asarray(result, dtype=np.int16)
