from dataclasses import dataclass

from cutemica.enums import ResolvedTheme

RgbColor = tuple[int, int, int]


@dataclass(frozen=True, slots=True)
class ResolvedMicaAltStyle:
    material_color: RgbColor
    tint_opacity: float
    luminosity_opacity: float
    blur_radius_dip: float
    fallback_color: RgbColor


@dataclass(frozen=True, slots=True)
class MicaAltRecipe:
    """Versioned CuteMica material recipe shared by every platform."""

    version: str = "mica-alt-v7-neighbor-halo"
    texture_scale: float = 0.25
    high_density_texture_scale: float = 0.5
    light_material: RgbColor = (218, 218, 218)
    light_tint_opacity: float = 0.5
    light_luminosity_opacity: float = 1.0
    light_fallback: RgbColor = (232, 232, 232)
    dark_material: RgbColor = (10, 10, 10)
    dark_tint_opacity: float = 0.0
    dark_luminosity_opacity: float = 1.0
    dark_fallback: RgbColor = (32, 32, 32)
    light_blur_radius_dip: float = 120.0
    dark_blur_radius_dip: float = 120.0
    high_density_light_blur_radius_dip: float = 116.0
    high_density_dark_blur_radius_dip: float = 115.0

    def texture_scale_for(self, device_pixel_ratio: float) -> float:
        """Use the validated higher-resolution approximation on scaled screens."""

        return (
            self.high_density_texture_scale
            if device_pixel_ratio > 1.0
            else self.texture_scale
        )

    def resolve(
        self,
        theme: ResolvedTheme,
        device_pixel_ratio: float = 1.0,
    ) -> ResolvedMicaAltStyle:
        high_density = device_pixel_ratio > 1.0
        if theme is ResolvedTheme.DARK:
            return ResolvedMicaAltStyle(
                material_color=self.dark_material,
                tint_opacity=self.dark_tint_opacity,
                luminosity_opacity=self.dark_luminosity_opacity,
                blur_radius_dip=(
                    self.high_density_dark_blur_radius_dip
                    if high_density
                    else self.dark_blur_radius_dip
                ),
                fallback_color=self.dark_fallback,
            )
        return ResolvedMicaAltStyle(
            material_color=self.light_material,
            tint_opacity=self.light_tint_opacity,
            luminosity_opacity=self.light_luminosity_opacity,
            blur_radius_dip=(
                self.high_density_light_blur_radius_dip
                if high_density
                else self.light_blur_radius_dip
            ),
            fallback_color=self.light_fallback,
        )
