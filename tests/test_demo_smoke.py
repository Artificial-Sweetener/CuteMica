from typing import cast

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QApplication

from cutemica.controller import MaterialController
from cutemica.demo.smoke import DemoSmokeSequence
from cutemica.demo.window import DemoWindow
from cutemica.enums import ResolvedTheme
from cutemica.theme import ThemeController


class _ApplicationStub(QObject):
    def __init__(self) -> None:
        super().__init__()
        self.exit_codes: list[int] = []

    def exit(self, code: int = 0) -> None:
        self.exit_codes.append(code)


class _ControllerStub(QObject):
    generation_finished = Signal(int)
    error = Signal(str)


class _ThemeStub:
    resolved = ResolvedTheme.DARK

    def set_mode(self, _mode: object) -> None:
        return


def test_smoke_fails_when_material_generation_fails() -> None:
    application = _ApplicationStub()
    controller = _ControllerStub()
    sequence = DemoSmokeSequence(
        cast(QApplication, application),
        cast(DemoWindow, object()),
        cast(ThemeController, _ThemeStub()),
        cast(MaterialController, controller),
        screenshot_path=None,
        exercise_theme_change=True,
    )
    sequence.start()

    controller.error.emit("decoder rejected source")
    controller.generation_finished.emit(1)

    assert sequence.error == "decoder rejected source"
    assert application.exit_codes == [1]
