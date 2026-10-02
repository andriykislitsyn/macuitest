"""Check the macOS privacy permissions macuitest needs before relying on them."""

from typing import Callable

import ApplicationServices
import Quartz

PERMISSIONS = ("Accessibility", "Screen Recording")
_granted: set[str] = set()


def require_screen_recording() -> None:
    """Raise unless this process may capture the screen.

    Raises:
        PermissionError: Screen Recording isn't granted.
    """
    _require(
        "Screen Recording",
        Quartz.CGPreflightScreenCaptureAccess,
        pane="Screen & System Audio Recording (Screen Recording before macOS 15)",
        # macOS applies a Screen Recording grant only after the app relaunches.
        then=", then restart that app",
    )


def require_accessibility() -> None:
    """Raise unless this process may read and control other apps' accessibility elements.

    Raises:
        PermissionError: Accessibility isn't granted.
    """
    _require("Accessibility", ApplicationServices.AXIsProcessTrusted, pane="Accessibility")


def _require(permission: str, check: Callable[[], bool], pane: str, then: str = "") -> None:
    # A grant is remembered, a denial isn't, so granting mid-run takes effect.
    if permission in _granted:
        return
    if not check():
        raise PermissionError(
            f"{permission} isn't granted. Grant it to the app running your tests in "
            f"System Settings > Privacy & Security > {pane}{then}."
        )
    _granted.add(permission)
