from pytestqt.qtbot import QtBot

from cutemica.enums import ResolvedTheme, ThemeMode
from cutemica.theme import ThemeController


def test_explicit_theme_modes_emit_only_when_resolved_theme_changes(
    qtbot: QtBot,
) -> None:
    controller = ThemeController(ThemeMode.LIGHT)

    with qtbot.waitSignal(controller.theme_changed, timeout=1_000) as signal:
        controller.set_mode(ThemeMode.DARK)

    assert controller.resolved is ResolvedTheme.DARK
    assert signal.args == [ResolvedTheme.DARK]
