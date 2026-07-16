"""D-Bus activation environment support for isolated desktop sessions."""

import subprocess


def update_dbus_activation_environment(
    environment: dict[str, str],
    variables: tuple[str, ...],
) -> None:
    """Publish compositor variables to subsequently activated services."""

    subprocess.run(
        ("dbus-update-activation-environment", *variables),
        env=environment,
        check=True,
        capture_output=True,
        text=True,
        timeout=5,
    )
