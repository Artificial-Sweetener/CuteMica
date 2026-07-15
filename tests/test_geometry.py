import pytest

from cutemica.geometry import Rect, ScreenBinding, bounding_rect


def test_rect_union_preserves_negative_virtual_desktop_coordinates() -> None:
    primary = Rect(0, 0, 3440, 1440)
    portrait = Rect(-2560, -242, 2560, 2880)

    result = bounding_rect((primary, portrait))

    assert result == Rect(-2560, -242, 6000, 2880)


def test_bounding_rect_requires_a_screen() -> None:
    with pytest.raises(ValueError, match="At least one"):
        bounding_rect(())


def test_physical_texture_scale_converts_to_texture_pixels_per_dip() -> None:
    binding = ScreenBinding(
        "portrait",
        Rect(0, 0, 150, 300),
        "portrait",
        Rect(0, 0, 100, 200),
        1.5,
    )

    assert binding.texture_pixels_per_dip(0.5) == 0.75
