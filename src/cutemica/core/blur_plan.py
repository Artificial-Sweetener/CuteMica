"""Resolve the blur backend and finite source support for a material field."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Literal

from cutemica.core.float_blur import gaussian_blur_support_pixels
from cutemica.core.speed_blur import (
    SPEED_BLUR_RADIUS_PIXELS,
    SPEED_BLUR_SUPPORT_PIXELS,
)
from cutemica.recipe import ResolvedMicaAltStyle

PaddingMode = Literal["reflect", "symmetric"]


class BlurBackend(Enum):
    SPEED = "speed"
    GAUSSIAN = "gaussian"


@dataclass(frozen=True, slots=True)
class BlurPlan:
    radius_pixels: float
    support_pixels: int
    padding_mode: PaddingMode
    backend: BlurBackend


def resolve_blur_plan(
    style: ResolvedMicaAltStyle,
    texture_pixels_per_dip: float,
) -> BlurPlan:
    """Resolve one backend plan shared by generation and field preparation."""

    radius = max(0.0, style.blur_radius_dip * texture_pixels_per_dip)
    if abs(radius - SPEED_BLUR_RADIUS_PIXELS) < 0.01:
        return BlurPlan(
            radius,
            SPEED_BLUR_SUPPORT_PIXELS,
            "reflect",
            BlurBackend.SPEED,
        )
    return BlurPlan(
        radius,
        gaussian_blur_support_pixels(radius),
        "symmetric",
        BlurBackend.GAUSSIAN,
    )
