from pathlib import Path

from cutemica.demo.main import _parse_arguments
from cutemica.diagnostics.startup_failure import redact_startup_text


def test_packaged_finder_process_serial_number_is_ignored() -> None:
    arguments = _parse_arguments(["-psn_0_12345", "--theme", "dark"])

    assert arguments.theme == "dark"


def test_startup_error_redacts_home_path_and_filename() -> None:
    message = redact_startup_text(
        f"Could not open {Path.home() / 'Pictures' / 'private-name.jpg'}\nNext line"
    )

    assert "private-name" not in message
    assert "Next line" in message
