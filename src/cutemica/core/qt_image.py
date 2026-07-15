from PIL import Image
from PySide6.QtGui import QImage


def pillow_to_qimage(image: Image.Image) -> QImage:
    rgba = image.convert("RGBA")
    data = rgba.tobytes("raw", "RGBA")
    qt_image = QImage(
        data,
        rgba.width,
        rgba.height,
        rgba.width * 4,
        QImage.Format.Format_RGBA8888,
    )
    return qt_image.copy()
