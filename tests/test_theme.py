from pytestqt.qtbot import QtBot

from cutemica.enums import ResolvedTheme, ThemeMode
from cutemica.theme import ThemeController


class MutableThemeProvider:
    name = "test system theme"

    def __init__(self, resolved: ResolvedTheme) -> None:
        self.resolved = resolved

    def resolve(self) -> ResolvedTheme:
        return self.resolved


def test_explicit_theme_modes_emit_only_when_resolved_theme_changes(
    qtbot: QtBot,
) -> None:
    controller = ThemeController(ThemeMode.LIGHT)

    with qtbot.waitSignal(controller.theme_changed, timeout=1_000) as signal:
        controller.set_mode(ThemeMode.DARK)

    assert controller.resolved.value == "dark"
    assert signal.args == [ResolvedTheme.DARK]


def test_auto_mode_uses_provider_and_publishes_polled_change(qtbot: QtBot) -> None:
    provider = MutableThemeProvider(ResolvedTheme.DARK)
    controller = ThemeController(ThemeMode.AUTO, provider=provider)

    assert controller.resolved is ResolvedTheme.DARK
    provider.resolved = ResolvedTheme.LIGHT
    assert controller._monitor is not None
    system_changes: list[ResolvedTheme] = []
    controller.system_theme_changed.connect(system_changes.append)
    with qtbot.waitSignal(controller.theme_changed, timeout=2_000) as signal:
        controller._monitor.poll()

    assert controller.resolved.value == "light"
    assert signal.args == [ResolvedTheme.LIGHT]
    assert system_changes == [ResolvedTheme.LIGHT]


def test_explicit_mode_still_reports_a_real_system_change(qtbot: QtBot) -> None:
    provider = MutableThemeProvider(ResolvedTheme.DARK)
    controller = ThemeController(ThemeMode.LIGHT, provider=provider)
    provider.resolved = ResolvedTheme.LIGHT
    assert controller._monitor is not None

    with qtbot.waitSignal(controller.system_theme_changed, timeout=2_000) as signal:
        controller._monitor.poll()

    assert signal.args == [ResolvedTheme.LIGHT]
    assert controller.resolved is ResolvedTheme.LIGHT
