from collections.abc import Iterable

from PySide6.QtGui import QScreen

from cutemica.geometry import Rect, ScreenBinding


def infer_qt_screen_bindings(
    screens: Iterable[QScreen],
) -> tuple[ScreenBinding, ...]:
    """Bind Qt screens to inferred native extents without mixing coordinate spaces."""
    bindings: list[ScreenBinding] = []
    for index, screen in enumerate(screens):
        qt_geometry = screen.geometry()
        dpr = screen.devicePixelRatio()
        qt_rect = Rect(
            qt_geometry.x(),
            qt_geometry.y(),
            qt_geometry.width(),
            qt_geometry.height(),
        )
        native_rect = Rect(
            qt_geometry.x(),
            qt_geometry.y(),
            round(qt_geometry.width() * dpr),
            round(qt_geometry.height() * dpr),
        )
        bindings.append(
            ScreenBinding(
                provider_screen_id=f"qt-screen-{index}:{screen.name()}",
                native_geometry_px=native_rect,
                qt_screen_name=screen.name(),
                qt_geometry_dip=qt_rect,
                device_pixel_ratio=dpr,
            )
        )
    return tuple(bindings)
