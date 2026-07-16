from PySide6.QtWidgets import QLabel
from pytestqt.qtbot import QtBot

from cutemica.demo.progress_panel import ProgressPanel
from cutemica.diagnostics.session import ValidationProgress


def test_progress_panel_praises_each_completed_activity(qtbot: QtBot) -> None:
    panel = ProgressPanel()
    qtbot.addWidget(panel)

    panel.set_progress(ValidationProgress(True, True, True, True))

    text = "\n".join(label.text() for label in panel.findChildren(QLabel))
    assert "Great — window movement captured!" in text
    assert "Nice — both monitors tested!" in text
    assert "Perfect — macOS appearance change detected!" in text
    assert "Got it — wallpaper change detected!" in text
    assert "Testing complete — thank you!" in text


def test_progress_panel_keeps_unfinished_activity_actionable(qtbot: QtBot) -> None:
    panel = ProgressPanel()
    qtbot.addWidget(panel)

    panel.set_progress(ValidationProgress(True, False, False, False))

    text = "\n".join(label.text() for label in panel.findChildren(QLabel))
    assert "✓ Great — window movement captured!" in text
    assert "○ Slowly drag across both monitors" in text
    assert "Complete each activity" in text
