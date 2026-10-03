"""Act on whole apps: the app-level verbs of the `macuitest` command.

Functions return values and raise typed errors. They never print.
"""

import subprocess
from typing import Any
from typing import Optional

import AppKit

from macuitest.lib.actions import NoWindowError
from macuitest.lib.core import wait_condition
from macuitest.lib.elements.locators.accessibility import GONE
from macuitest.lib.elements.locators.accessibility import alive
from macuitest.lib.elements.locators.accessibility import app_root
from macuitest.lib.elements.native.native_ui_element import NativeUIElement

# Seconds to wait for a launched app's window, and for a quitting app to exit.
LAUNCH_TIMEOUT: float = 15
QUIT_TIMEOUT: float = 10


class LaunchError(RuntimeError):
    """The app couldn't be opened."""


class QuitError(RuntimeError):
    """The app is still running after it was asked to quit."""


def launch(app: str, timeout: float = LAUNCH_TIMEOUT) -> None:
    """Open `app`, or bring it forward when it runs, and wait until it has a window.

    Raises:
        LaunchError: `open` can't open `app`, such as an unknown name.
        NoWindowError: `app` has no window within `timeout` seconds.
    """
    result = subprocess.run(["open", "-a", app], capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise LaunchError(result.stderr.strip() or f"Can't open {app}")
    # Some apps, such as Calculator, show their windows only while active.
    if not wait_condition(lambda: _activate(app), timeout=timeout):
        raise NoWindowError(f"{app} is running but has no window")


def quit(app: str, timeout: float = QUIT_TIMEOUT) -> bool:
    """Ask `app` to quit, like Command-Q, and wait until it exits.

    Returns:
        False when `app` wasn't running.

    Raises:
        QuitError: `app` still runs after `timeout` seconds, such as while it asks to save.
    """
    applications = running(app)
    if not applications:
        return False
    pids = [application.processIdentifier() for application in applications]
    for application in applications:
        application.terminate()
    if not wait_condition(lambda: not any(alive(pid) for pid in pids), timeout=timeout):
        raise QuitError(
            f"{app} is still running. It may be asking to save: answer it with find and press."
        )
    return True


def running(app: str) -> list[Any]:
    """Return the running applications named `app`."""
    workspace = AppKit.NSWorkspace.sharedWorkspace()
    return [a for a in workspace.runningApplications() if a.localizedName() == app]


def app_element(app: str) -> Optional[NativeUIElement]:
    """Return the accessibility element of running app `app`, windows or not, or None."""
    applications = running(app)
    if not applications:
        return None
    return NativeUIElement.from_pid(applications[0].processIdentifier())


def _activate(app: str) -> bool:
    root = app_root(app)
    if root is None:
        return False
    try:
        root.activate()
    except GONE:
        return False
    return True
