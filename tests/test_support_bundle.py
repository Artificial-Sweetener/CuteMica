import json
from pathlib import Path
from zipfile import ZipFile

from cutemica.diagnostics.support_bundle import SupportBundleWriter


def test_support_bundle_redacts_sensitive_values(tmp_path: Path) -> None:
    report: dict[str, object] = {
        "wallpaper": {"provider": "macos-appkit"},
        "session": {
            "errors": [
                {"message": "/Users/tester/Pictures/secret-wallpaper.png failed"}
            ]
        },
    }

    output = SupportBundleWriter().write(
        report,
        tmp_path,
        sensitive_values=(
            "/Users/tester/Pictures/secret-wallpaper.png",
            "/Users/tester",
        ),
    )

    with ZipFile(output) as archive:
        report_text = archive.read("report.json").decode()
        payload = json.loads(report_text)
        readme = archive.read("README.txt").decode()
    assert "secret-wallpaper" not in report_text
    assert "/Users/tester" not in report_text
    assert payload["session"]["errors"][0]["message"] == "<redacted> failed"
    assert "does not contain the wallpaper image" in readme


def test_support_bundle_redacts_other_home_relative_paths(tmp_path: Path) -> None:
    private_path = Path.home() / "Pictures" / "previous-private-wallpaper.jpg"
    report: dict[str, object] = {"error": f"Could not decode {private_path}"}

    output = SupportBundleWriter().write(
        report,
        tmp_path,
        sensitive_values=(str(Path.home()),),
    )

    with ZipFile(output) as archive:
        report_text = archive.read("report.json").decode()
    assert "previous-private-wallpaper" not in report_text
    assert "<redacted-path>" in report_text
