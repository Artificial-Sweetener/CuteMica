import pytest

from cutemica.geometry import FloatRect, Rect, ScreenBinding, WindowGeometry
from cutemica.viewport import plan_material_slices


def binding(identifier: str, geometry: Rect, dpr: float = 1.0) -> ScreenBinding:
    return ScreenBinding(identifier, geometry, identifier, geometry, dpr)


def mixed_dpi_bindings() -> tuple[ScreenBinding, ScreenBinding]:
    portrait = ScreenBinding(
        "portrait",
        Rect(-2560, -242, 2560, 2880),
        "portrait",
        Rect(-2560, -242, 1707, 1920),
        1.5,
    )
    primary = ScreenBinding(
        "primary",
        Rect(0, 0, 3440, 1440),
        "primary",
        Rect(0, 0, 3440, 1440),
        1.0,
    )
    return portrait, primary


def test_quarter_scale_preserves_every_subpixel_motion_phase() -> None:
    screen = binding("primary", Rect(0, 0, 3440, 1440))
    sizes = {screen.cache_key: (860, 360)}

    source_positions = [
        plan_material_slices(
            WindowGeometry(FloatRect(x, 100, 980, 680), 980, 680),
            (screen,),
            sizes,
        )[0].source.x
        for x in range(4)
    ]

    assert source_positions == pytest.approx([0.0, 0.25, 0.5, 0.75])


def test_window_spanning_screens_gets_one_registered_slice_per_screen() -> None:
    left = binding("left", Rect(-1000, 0, 1000, 800))
    right = binding("right", Rect(0, 0, 1200, 800))
    sizes = {
        left.cache_key: (500, 400),
        right.cache_key: (300, 200),
    }

    slices = plan_material_slices(
        WindowGeometry(FloatRect(-200, 100, 500, 400), 500, 400),
        (left, right),
        sizes,
    )

    assert len(slices) == 2
    assert slices[0].target == FloatRect(0, 0, 200, 400)
    assert slices[0].source.x == pytest.approx(400.0)
    assert slices[1].target == FloatRect(200, 0, 300, 400)
    assert slices[1].source.x == pytest.approx(0.0)
    assert slices[1].source.width == pytest.approx(75.0)


def test_missing_material_leaves_that_screen_for_fallback_painting() -> None:
    left = binding("left", Rect(0, 0, 100, 100))
    right = binding("right", Rect(100, 0, 100, 100))

    slices = plan_material_slices(
        WindowGeometry(FloatRect(50, 0, 100, 100), 100, 100),
        (left, right),
        {left.cache_key: (50, 50)},
    )

    assert [item.screen_key for item in slices] == [left.cache_key]
    assert slices[0].target == FloatRect(0, 0, 50, 100)


def test_mixed_dpi_qt_coordinate_gap_is_fully_covered_in_native_space() -> None:
    portrait, primary = mixed_dpi_bindings()
    sizes = {
        portrait.cache_key: (1280, 1440),
        primary.cache_key: (860, 360),
    }

    slices = plan_material_slices(
        WindowGeometry(FloatRect(-299.5, 100, 900, 600), 600, 400),
        (portrait, primary),
        sizes,
    )

    assert len(slices) == 2
    assert slices[0].target.x == pytest.approx(0.0)
    assert slices[0].target.width == pytest.approx(199.6666667)
    assert slices[1].target.x == pytest.approx(199.6666667)
    assert slices[1].target.width == pytest.approx(400.3333333)
    assert sum(item.target.width for item in slices) == pytest.approx(600.0)


def test_dpi_handoff_preserves_sources_for_the_same_native_window() -> None:
    portrait, primary = mixed_dpi_bindings()
    sizes = {
        portrait.cache_key: (1280, 1440),
        primary.cache_key: (860, 360),
    }
    native_rect = FloatRect(-300, 100, 900, 600)

    before = plan_material_slices(
        WindowGeometry(native_rect, 600, 400),
        (portrait, primary),
        sizes,
    )
    after = plan_material_slices(
        WindowGeometry(native_rect, 900, 600),
        (portrait, primary),
        sizes,
    )

    assert [item.source for item in before] == [item.source for item in after]
    assert sum(item.target.width for item in before) == pytest.approx(600)
    assert sum(item.target.width for item in after) == pytest.approx(900)
