"""Invoke the native drag probe inside an already-running desktop session."""

from __future__ import annotations

import json
import subprocess
import sys


def assert_native_drag_contract(
    environment: dict[str, str],
    expected_registration: str,
) -> dict[str, object]:
    """Require native timing budgets and rendered-frame continuity."""

    completed = subprocess.run(
        (
            sys.executable,
            "-m",
            "cutemica.performance.native_drag",
            "--frames",
            "240",
            "--stability-frames",
            "64",
        ),
        env=environment,
        capture_output=True,
        text=True,
        timeout=60,
    )
    if completed.returncode:
        raise AssertionError(
            f"Native drag contract failed:\n{completed.stdout}\n{completed.stderr}"
        )
    lines = completed.stdout.splitlines()
    if not lines or "CUTEMICA_NATIVE_DRAG_OK" not in lines:
        raise AssertionError(
            f"Native drag evidence marker missing:\n{completed.stdout}"
        )
    payload = json.loads(lines[0])
    if not isinstance(payload, dict):
        raise AssertionError("Native drag evidence was not a JSON object")
    if payload.get("registration") != expected_registration:
        raise AssertionError(
            f"Expected {expected_registration!r} drag registration, got "
            f"{payload.get('registration')!r}"
        )
    print(completed.stdout.strip(), flush=True)
    return payload
