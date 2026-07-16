from PySide6.QtCore import QRect
from PySide6.QtGui import QColor, QImage, QPainter, QPixmap
from pytestqt.qtbot import QtBot

from cutemica.geometry import FloatRect, Rect, ScreenBinding, WindowGeometry
from cutemica.viewport import plan_material_slices
from cutemica.widgets.material_painter import paint_material_slices


def test_smooth_sampling_represents_each_quarter_scale_motion_phase(
    qtbot: QtBot,
) -> None:
    del qtbot
    image = QImage(16, 4, QImage.Format.Format_RGB32)
    for y in range(image.height()):
        for x in range(image.width()):
            image.setPixelColor(x, y, QColor(x * 16, 0, 0))
    material = QPixmap.fromImage(image)
    screen_geometry = Rect(0, 0, 64, 16)
    binding = ScreenBinding(
        "screen",
        screen_geometry,
        "screen",
        screen_geometry,
        1.0,
    )
    images = {binding.cache_key: material}
    sizes = {binding.cache_key: material.size().toTuple()}
    sampled_values = []
    for x in range(4):
        target = QImage(32, 8, QImage.Format.Format_RGB32)
        painter = QPainter(target)
        paint_material_slices(
            painter,
            QRect(0, 0, target.width(), target.height()),
            (0, 0, 0),
            plan_material_slices(
                WindowGeometry(FloatRect(x, 0, 32, 8), 32, 8),
                (binding,),
                sizes,
            ),
            images,
        )
        painter.end()
        sampled_values.append(target.pixelColor(16, 4).red())

    assert sampled_values == sorted(sampled_values)
    assert len(set(sampled_values)) == 4


def test_spanning_window_paints_each_screen_material_in_its_own_slice(
    qtbot: QtBot,
) -> None:
    del qtbot
    left_geometry = Rect(0, 0, 100, 100)
    right_geometry = Rect(100, 0, 100, 100)
    left = ScreenBinding("left", left_geometry, "left", left_geometry, 1.0)
    right = ScreenBinding("right", right_geometry, "right", right_geometry, 1.0)
    left_material = QPixmap(50, 50)
    right_material = QPixmap(50, 50)
    left_material.fill(QColor(200, 20, 30))
    right_material.fill(QColor(30, 40, 210))
    materials = {
        left.cache_key: left_material,
        right.cache_key: right_material,
    }
    sizes = {key: material.size().toTuple() for key, material in materials.items()}
    target = QImage(100, 60, QImage.Format.Format_RGB32)
    painter = QPainter(target)
    paint_material_slices(
        painter,
        target.rect(),
        (0, 0, 0),
        plan_material_slices(
            WindowGeometry(FloatRect(50, 20, 100, 60), 100, 60),
            (left, right),
            sizes,
        ),
        materials,
    )
    painter.end()

    assert target.pixelColor(20, 30) == QColor(200, 20, 30)
    assert target.pixelColor(80, 30) == QColor(30, 40, 210)


def test_mixed_dpi_monitor_boundary_contains_no_fallback_pixels(
    qtbot: QtBot,
) -> None:
    del qtbot
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
    portrait_material = QPixmap(128, 144)
    primary_material = QPixmap(86, 36)
    portrait_material.fill(QColor(200, 20, 30))
    primary_material.fill(QColor(30, 40, 210))
    materials = {
        portrait.cache_key: portrait_material,
        primary.cache_key: primary_material,
    }
    sizes = {key: material.size().toTuple() for key, material in materials.items()}
    target = QImage(600, 400, QImage.Format.Format_RGB32)
    fallback = QColor(37, 37, 37)
    painter = QPainter(target)
    paint_material_slices(
        painter,
        target.rect(),
        (37, 37, 37),
        plan_material_slices(
            WindowGeometry(FloatRect(-299.5, 100, 900, 600), 600, 400),
            (portrait, primary),
            sizes,
        ),
        materials,
    )
    painter.end()

    assert target.pixelColor(100, 200) == QColor(200, 20, 30)
    assert target.pixelColor(400, 200) == QColor(30, 40, 210)
    assert all(target.pixelColor(x, 200) != fallback for x in range(target.width()))


def test_window_edge_sampling_remains_registered_during_motion(
    qtbot: QtBot,
) -> None:
    del qtbot
    image = QImage(100, 35, QImage.Format.Format_RGB32)
    image.fill(QColor(40, 100, 140))
    for y in range(image.height()):
        image.setPixelColor(65, y, QColor(238, 214, 91))
    material = QPixmap.fromImage(image)
    geometry = Rect(0, 0, 400, 140)
    binding = ScreenBinding("screen", geometry, "screen", geometry, 1.0)
    materials = {binding.cache_key: material}
    sizes = {binding.cache_key: material.size().toTuple()}

    previous = _registered_frame(160, binding, sizes, materials)
    current = _registered_frame(161, binding, sizes, materials)

    for y in range(current.height()):
        for x in range(current.width() - 1):
            assert current.pixelColor(x, y) == previous.pixelColor(x + 1, y)


def _registered_frame(
    native_x: int,
    binding: ScreenBinding,
    sizes: dict[str, tuple[int, int]],
    materials: dict[str, QPixmap],
) -> QImage:
    target = QImage(100, 70, QImage.Format.Format_RGB32)
    painter = QPainter(target)
    paint_material_slices(
        painter,
        target.rect(),
        (0, 0, 0),
        plan_material_slices(
            WindowGeometry(FloatRect(native_x, 0, 100, 70), 100, 70),
            (binding,),
            sizes,
        ),
        materials,
        paint_bounds=target.rect(),
    )
    painter.end()
    return target
