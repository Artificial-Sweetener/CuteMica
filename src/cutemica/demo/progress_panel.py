"""Friendly automatic feedback for an interactive tester."""

from __future__ import annotations

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from cutemica.diagnostics.session import ValidationProgress


class ProgressPanel(QWidget):
    """Present evidence-backed validation milestones without technical detail."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        heading = QLabel("Your test progress")
        heading.setObjectName("progressHeading")
        self._movement = QLabel()
        self._monitors = QLabel()
        self._appearance = QLabel()
        self._wallpaper = QLabel()
        self._thanks = QLabel()
        self._thanks.setObjectName("completionThanks")
        self._thanks.setWordWrap(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(7)
        layout.addWidget(heading)
        layout.addWidget(self._movement)
        layout.addWidget(self._monitors)
        layout.addWidget(self._appearance)
        layout.addWidget(self._wallpaper)
        layout.addWidget(self._thanks)
        self.set_progress(ValidationProgress(False, False, False, False))

    def set_progress(self, progress: ValidationProgress) -> None:
        """Refresh all milestone messages from one immutable snapshot."""

        self._movement.setText(
            _message(
                progress.movement_complete,
                "Drag this window around",
                "Great — window movement captured!",
            )
        )
        self._monitors.setText(
            _message(
                progress.monitors_complete,
                "Slowly drag across both monitors",
                "Nice — both monitors tested!",
            )
        )
        self._appearance.setText(
            _message(
                progress.appearance_complete,
                "Switch macOS between Light and Dark",
                "Perfect — macOS appearance change detected!",
            )
        )
        self._wallpaper.setText(
            _message(
                progress.wallpaper_complete,
                "Change the desktop wallpaper",
                "Got it — wallpaper change detected!",
            )
        )
        self._thanks.setText(
            "🎉 Testing complete — thank you! You did a great job. "
            "Save the report below and send it back."
            if progress.complete
            else "Complete each activity and CuteMica will detect it automatically."
        )


def _message(complete: bool, waiting: str, success: str) -> str:
    return f"✓ {success}" if complete else f"○ {waiting}"
