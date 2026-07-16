from pathlib import Path
from subprocess import CompletedProcess

import pytest

from cutemica.providers import qt_dbus


def test_qt_dbus_prefers_a_command_on_path(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "cutemica.providers.qt_dbus.shutil.which",
        lambda name: "/usr/bin/qdbus6" if name == "qdbus6" else None,
    )

    assert qt_dbus.qt_dbus_executable() == "/usr/bin/qdbus6"


def test_qt_dbus_uses_qtpaths_binary_directory(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    binary_directory = tmp_path / "lib64" / "qt6" / "bin"
    binary_directory.mkdir(parents=True)
    qdbus = binary_directory / "qdbus"
    qdbus.touch()
    monkeypatch.setattr(
        "cutemica.providers.qt_dbus.shutil.which",
        lambda name: "/usr/bin/qtpaths6" if name == "qtpaths6" else None,
    )
    monkeypatch.setattr(
        "cutemica.providers.qt_dbus.subprocess.run",
        lambda *_args, **_kwargs: CompletedProcess(
            args=("qtpaths6",),
            returncode=0,
            stdout=str(binary_directory),
        ),
    )

    assert qt_dbus.qt_dbus_executable() == str(qdbus)


def test_qt_dbus_reports_a_missing_runtime(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("cutemica.providers.qt_dbus.shutil.which", lambda _name: None)

    with pytest.raises(RuntimeError, match="requires qdbus"):
        qt_dbus.qt_dbus_executable()
