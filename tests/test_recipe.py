from cutemica.enums import ResolvedTheme
from cutemica.recipe import MicaAltRecipe


def test_recipe_resolves_distinct_opaque_fallbacks_for_each_theme() -> None:
    recipe = MicaAltRecipe()

    light = recipe.resolve(ResolvedTheme.LIGHT)
    dark = recipe.resolve(ResolvedTheme.DARK)

    assert light.material_color == recipe.light_material
    assert dark.material_color == recipe.dark_material
    assert light.fallback_color != dark.fallback_color
    assert light.material_color != dark.material_color
    assert 0 < light.tint_opacity < 1
    assert dark.tint_opacity == 0
    assert light.luminosity_opacity == 1
    assert dark.luminosity_opacity == 1


def test_versioned_dual_theme_constants_remain_distinct() -> None:
    recipe = MicaAltRecipe()

    light = recipe.resolve(ResolvedTheme.LIGHT)
    dark = recipe.resolve(ResolvedTheme.DARK)

    assert recipe.version == "mica-alt-v7-neighbor-halo"
    assert recipe.texture_scale == 0.25
    assert (light.material_color, light.tint_opacity) == ((218, 218, 218), 0.5)
    assert light.blur_radius_dip == 120.0
    assert (dark.material_color, dark.tint_opacity) == ((10, 10, 10), 0.0)
    assert dark.blur_radius_dip == 120.0


def test_scaled_screen_uses_validated_high_density_recipe() -> None:
    recipe = MicaAltRecipe()

    light = recipe.resolve(ResolvedTheme.LIGHT, 1.5)
    dark = recipe.resolve(ResolvedTheme.DARK, 1.5)

    assert recipe.texture_scale_for(1.5) == 0.5
    assert light.blur_radius_dip == 116.0
    assert dark.blur_radius_dip == 115.0


def test_half_resolution_4k_texture_fits_the_per_screen_memory_budget() -> None:
    texture_scale = MicaAltRecipe().texture_scale_for(1.5)
    texture_bytes = round(3840 * texture_scale) * round(2160 * texture_scale) * 4

    assert texture_bytes <= 8 * 1024**2
