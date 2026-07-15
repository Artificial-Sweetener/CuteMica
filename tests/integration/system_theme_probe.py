"""Print the system theme resolved by CuteMica in a real Qt application."""

from PySide6.QtGui import QGuiApplication

from cutemica.enums import ThemeMode
from cutemica.theme import ThemeController

application = QGuiApplication([])
controller = ThemeController(ThemeMode.AUTO)
print(controller.resolved.name.title())
application.quit()
