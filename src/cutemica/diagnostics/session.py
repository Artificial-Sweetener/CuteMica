"""Bounded measurements from a visible, user-driven validation session."""

from __future__ import annotations

from collections import deque
from datetime import UTC, datetime
from math import ceil
from statistics import median
from time import perf_counter

from cutemica.enums import ResolvedTheme
from cutemica.geometry import ScreenBinding, WindowGeometry


class ValidationSession:
    """Record live movement and environment changes without retaining images."""

    def __init__(
        self,
        bindings: tuple[ScreenBinding, ...],
        initial_theme: ResolvedTheme,
        initial_wallpaper_provider: str,
    ) -> None:
        self._bindings = bindings
        self._current_theme = initial_theme
        self._current_wallpaper_provider = initial_wallpaper_provider
        self._samples_limit = 10_000
        self.reset()

    def reset(self) -> None:
        """Begin a fresh interactive test while preserving host configuration."""

        self._started_at = datetime.now(UTC)
        self._started_clock = perf_counter()
        self._move_cycle_ms: deque[float] = deque(maxlen=self._samples_limit)
        self._geometry_ms: deque[float] = deque(maxlen=self._samples_limit)
        self._presentation_ms: deque[float] = deque(maxlen=self._samples_limit)
        self._paint_ms: deque[float] = deque(maxlen=self._samples_limit)
        self._move_events = 0
        self._screen_transitions = 0
        self._theme_changes = 0
        self._wallpaper_changes = 0
        self._generation_count = 0
        self._errors: deque[dict[str, object]] = deque(maxlen=200)
        self._events: deque[dict[str, object]] = deque(maxlen=500)
        self._last_screen_set: tuple[str, ...] = ()
        self._last_theme = self._current_theme
        self._themes_seen = {self._current_theme.value}
        self._wallpaper_providers_seen = {self._current_wallpaper_provider}
        self._record_event("session-started")

    def record_motion(
        self,
        geometry: WindowGeometry,
        *,
        move_cycle_ms: float,
        geometry_ms: float,
        presentation_ms: float,
        paint_ms: float,
    ) -> None:
        """Record one real move event and the screens covered by the window."""

        self._move_events += 1
        self._move_cycle_ms.append(move_cycle_ms)
        self._geometry_ms.append(geometry_ms)
        self._presentation_ms.append(presentation_ms)
        self._paint_ms.append(paint_ms)
        screen_set = self._intersecting_screens(geometry)
        if self._last_screen_set and screen_set != self._last_screen_set:
            self._screen_transitions += 1
            self._record_event(
                "screen-transition",
                screens=list(screen_set),
            )
        self._last_screen_set = screen_set

    def record_theme(self, theme: ResolvedTheme) -> None:
        """Record a resolved appearance transition."""

        if theme is self._last_theme:
            return
        self._last_theme = theme
        self._current_theme = theme
        self._themes_seen.add(theme.value)
        self._theme_changes += 1
        self._record_event("theme-changed", theme=theme.value)

    def record_wallpaper_change(self, provider_name: str) -> None:
        """Record wallpaper publication without retaining its source path."""

        self._wallpaper_changes += 1
        self._current_wallpaper_provider = provider_name
        self._wallpaper_providers_seen.add(provider_name)
        self._record_event("wallpaper-changed", provider=provider_name)

    def record_generation(self, generation: int, elapsed_ms: float) -> None:
        """Record completion of one material generation."""

        self._generation_count += 1
        self._record_event(
            "material-ready",
            generation=generation,
            elapsed_ms=round(elapsed_ms, 3),
        )

    def record_error(self, area: str, message: str) -> None:
        """Retain a bounded error record for the exported support bundle."""

        error = {
            "elapsed_ms": self._elapsed_ms(),
            "area": area,
            "message": message,
        }
        self._errors.append(error)
        self._events.append({"event": "error", **error})

    @property
    def status_text(self) -> str:
        """Return a compact progress line for the tester UI."""

        return (
            f"Moves {self._move_events} · monitor transitions "
            f"{self._screen_transitions} · appearance changes {self._theme_changes} · "
            f"wallpaper changes {self._wallpaper_changes}"
        )

    def payload(self) -> dict[str, object]:
        """Return JSON-compatible measurements for a support report."""

        return {
            "started_at_utc": self._started_at.isoformat(),
            "duration_ms": self._elapsed_ms(),
            "move_events": self._move_events,
            "screen_transitions": self._screen_transitions,
            "theme_changes": self._theme_changes,
            "wallpaper_changes": self._wallpaper_changes,
            "material_generations": self._generation_count,
            "themes_seen": sorted(self._themes_seen),
            "wallpaper_providers_seen": sorted(self._wallpaper_providers_seen),
            "move_cycle": _timing_payload(self._move_cycle_ms),
            "geometry": _timing_payload(self._geometry_ms),
            "presentation": _timing_payload(self._presentation_ms),
            "paint": _timing_payload(self._paint_ms),
            "errors": list(self._errors),
            "events": list(self._events),
        }

    def _intersecting_screens(self, geometry: WindowGeometry) -> tuple[str, ...]:
        window = geometry.native_rect_px
        return tuple(
            binding.qt_screen_name
            for binding in self._bindings
            if window.x < binding.native_geometry_px.right
            and window.right > binding.native_geometry_px.x
            and window.y < binding.native_geometry_px.bottom
            and window.bottom > binding.native_geometry_px.y
        )

    def _record_event(self, event: str, **details: object) -> None:
        self._events.append(
            {
                "elapsed_ms": self._elapsed_ms(),
                "event": event,
                **details,
            }
        )

    def _elapsed_ms(self) -> float:
        return round((perf_counter() - self._started_clock) * 1_000, 3)


def _timing_payload(samples: deque[float]) -> dict[str, object]:
    if not samples:
        return {"sample_count": 0}
    ordered = sorted(samples)
    return {
        "sample_count": len(ordered),
        "median_ms": round(median(ordered), 4),
        "p95_ms": round(ordered[ceil(len(ordered) * 0.95) - 1], 4),
        "maximum_ms": round(ordered[-1], 4),
    }
