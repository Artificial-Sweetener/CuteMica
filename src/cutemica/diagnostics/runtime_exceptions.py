"""Route otherwise invisible Qt callback failures into tester diagnostics."""

from __future__ import annotations

import sys
import traceback
from collections.abc import Callable
from types import TracebackType

from cutemica.diagnostics.session import ValidationSession

ExceptionHook = Callable[
    [type[BaseException], BaseException, TracebackType | None], None
]


def install_exception_recorder(session: ValidationSession) -> ExceptionHook:
    """Install an exception hook and return the hook it replaced."""

    previous = sys.excepthook

    def record_exception(
        exception_type: type[BaseException],
        exception: BaseException,
        exception_traceback: TracebackType | None,
    ) -> None:
        formatted = "".join(
            traceback.format_exception(
                exception_type,
                exception,
                exception_traceback,
            )
        )
        session.record_error("unhandled-callback", formatted)
        previous(exception_type, exception, exception_traceback)

    sys.excepthook = record_exception
    return previous
