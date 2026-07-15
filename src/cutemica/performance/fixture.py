"""Deterministic material and display fixture for motion measurements."""

from PySide6.QtGui import QColor, QImage, QLinearGradient, QPainter

from cutemica.geometry import Rect, ScreenBinding


def create_motion_material() -> QImage:
    """Create a deterministic reduced-resolution wallpaper material."""

    image = QImage(860, 360, QImage.Format.Format_RGB32)
    gradient = QLinearGradient(0, 0, image.width(), image.height())
    gradient.setColorAt(0.0, QColor(14, 28, 70))
    gradient.setColorAt(0.5, QColor(104, 36, 92))
    gradient.setColorAt(1.0, QColor(20, 72, 58))
    painter = QPainter(image)
    painter.fillRect(image.rect(), gradient)
    painter.end()
    return image


def create_motion_binding() -> ScreenBinding:
    """Create the deterministic 3440-by-1440 benchmark display."""

    geometry = Rect(0, 0, 3440, 1440)
    return ScreenBinding("benchmark", geometry, "benchmark", geometry, 1.0)
