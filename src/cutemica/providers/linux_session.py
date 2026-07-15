"""Linux session capability detection."""

import os

from cutemica.providers.capabilities import WindowRegistration


def linux_window_registration() -> WindowRegistration:
    """Report whether the current Linux session exposes global window geometry."""

    if os.environ.get("XDG_SESSION_TYPE", "").casefold() == "wayland":
        return WindowRegistration.SCREEN_LOCAL
    return WindowRegistration.GLOBAL
