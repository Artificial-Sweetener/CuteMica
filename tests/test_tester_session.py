from cutemica.diagnostics.session import ValidationSession
from cutemica.enums import ResolvedTheme
from cutemica.geometry import FloatRect, Rect, ScreenBinding, WindowGeometry


def test_session_records_cross_monitor_motion_and_timing() -> None:
    session = ValidationSession(_bindings(), ResolvedTheme.LIGHT, "macos-appkit")

    session.record_motion(
        WindowGeometry(FloatRect(100, 20, 400, 300), 400, 300),
        move_cycle_ms=1.2,
        geometry_ms=0.1,
        presentation_ms=1.0,
        paint_ms=0.4,
    )
    session.record_motion(
        WindowGeometry(FloatRect(1700, 20, 400, 300), 400, 300),
        move_cycle_ms=1.4,
        geometry_ms=0.2,
        presentation_ms=1.1,
        paint_ms=0.5,
    )
    session.record_motion(
        WindowGeometry(FloatRect(2100, 20, 400, 300), 400, 300),
        move_cycle_ms=1.3,
        geometry_ms=0.1,
        presentation_ms=1.0,
        paint_ms=0.4,
    )

    payload = session.payload()
    assert payload["move_events"] == 3
    assert payload["screen_transitions"] == 2
    assert payload["move_cycle"] == {
        "sample_count": 3,
        "median_ms": 1.3,
        "p95_ms": 1.4,
        "maximum_ms": 1.4,
    }


def test_session_counts_repeated_appearance_transitions() -> None:
    session = ValidationSession(_bindings(), ResolvedTheme.LIGHT, "macos-appkit")

    session.record_theme(ResolvedTheme.DARK)
    session.record_theme(ResolvedTheme.LIGHT)

    assert session.payload()["theme_changes"] == 2
    assert session.payload()["themes_seen"] == ["dark", "light"]

    session.reset()

    assert session.payload()["themes_seen"] == ["light"]


def _bindings() -> tuple[ScreenBinding, ...]:
    return (
        ScreenBinding(
            "left", Rect(0, 0, 1920, 1080), "Left", Rect(0, 0, 1920, 1080), 1
        ),
        ScreenBinding(
            "right",
            Rect(1920, 0, 2560, 1440),
            "Right",
            Rect(1920, 0, 1280, 720),
            2,
        ),
    )
