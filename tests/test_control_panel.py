from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QLabel

from cutemica.demo.control_panel import ControlPanel


def test_dark_panel_gives_every_label_explicit_light_text(qtbot: object) -> None:
    panel = ControlPanel("Environment")
    panel.set_theme_style(dark=True)
    panel.ensurePolished()

    colors = {
        label.palette().color(QPalette.ColorRole.WindowText).name()
        for label in panel.findChildren(QLabel)
    }

    assert colors == {QColor("#f3f3f3").name()}
