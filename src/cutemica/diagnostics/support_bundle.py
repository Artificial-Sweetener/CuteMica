"""Export a compact report that a tester can send without inspection."""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


class SupportBundleWriter:
    """Write redacted JSON diagnostics into a shareable ZIP archive."""

    def write(
        self,
        report: dict[str, object],
        destination: Path,
        *,
        sensitive_values: tuple[str, ...] = (),
    ) -> Path:
        """Create a timestamped support bundle in the destination directory."""

        destination.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%SZ")
        output = destination / f"CuteMica-test-report-{timestamp}.zip"
        redacted = _redact(report, sensitive_values)
        with ZipFile(output, "w", compression=ZIP_DEFLATED) as archive:
            archive.writestr(
                "report.json",
                json.dumps(redacted, indent=2, sort_keys=True) + "\n",
            )
            archive.writestr("README.txt", _BUNDLE_README)
        return output


def _redact(value: object, sensitive_values: tuple[str, ...]) -> object:
    if isinstance(value, str):
        result = value
        for sensitive in sensitive_values:
            if sensitive:
                result = result.replace(sensitive, "<redacted>")
        return re.sub(
            r"<redacted>[/\\][^\n\r\"']+",
            "<redacted-path>",
            result,
        )
    if isinstance(value, dict):
        return {
            str(key): _redact(item, sensitive_values) for key, item in value.items()
        }
    if isinstance(value, list | tuple):
        return [_redact(item, sensitive_values) for item in value]
    return value


_BUNDLE_README = """CuteMica tester support bundle

Send this ZIP file to the CuteMica developer. It contains runtime, display,
performance, and test-event metadata. It does not contain the wallpaper image,
a screenshot, the wallpaper filename, or the wallpaper path.
"""
