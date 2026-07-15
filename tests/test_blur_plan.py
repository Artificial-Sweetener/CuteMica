from cutemica.core.blur_plan import BlurBackend, resolve_blur_plan
from cutemica.enums import ResolvedTheme
from cutemica.recipe import MicaAltRecipe


def test_quarter_scale_recipe_uses_the_phase_aware_speed_support() -> None:
    recipe = MicaAltRecipe()

    plan = resolve_blur_plan(
        recipe.resolve(ResolvedTheme.DARK),
        texture_pixels_per_dip=0.25,
    )

    assert plan.backend is BlurBackend.SPEED
    assert plan.radius_pixels == 30.0
    assert plan.support_pixels == 81
    assert plan.padding_mode == "reflect"


def test_high_density_recipe_reports_its_complete_gaussian_support() -> None:
    recipe = MicaAltRecipe()

    plan = resolve_blur_plan(
        recipe.resolve(ResolvedTheme.DARK, 1.5),
        texture_pixels_per_dip=0.75,
    )

    assert plan.backend is BlurBackend.GAUSSIAN
    assert plan.radius_pixels == 86.25
    assert plan.support_pixels == 258
    assert plan.padding_mode == "symmetric"
