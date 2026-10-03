"""Act on whole apps: the app-level verbs of the `macuitest` command.

Functions return values and raise typed errors. They never print.
"""

import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any
from typing import Optional

import AppKit
import Quartz

from macuitest.lib.actions import ActionError
from macuitest.lib.actions import FocusError
from macuitest.lib.actions import NoWindowError
from macuitest.lib.actions import UsageError
from macuitest.lib.actions import bring_to_front
from macuitest.lib.core import wait_condition
from macuitest.lib.elements.controllers.keyboard_controller import keyboard
from macuitest.lib.elements.controllers.keyboard_mappings import KEYBOARD_KEYS
from macuitest.lib.elements.locators.accessibility import GONE
from macuitest.lib.elements.locators.accessibility import AXQuery
from macuitest.lib.elements.locators.accessibility import alive
from macuitest.lib.elements.locators.accessibility import app_root
from macuitest.lib.elements.locators.accessibility import frame_of
from macuitest.lib.elements.locators.accessibility import standard_window
from macuitest.lib.elements.locators.capture import window_number
from macuitest.lib.elements.locators.capture import write_png
from macuitest.lib.elements.locators.screen import snake_case
from macuitest.lib.elements.native.native_ui_element import NativeUIElement
from macuitest.lib.elements.ui.monitor import monitor

# Seconds to wait for a launched app's window, and for a quitting app to exit.
LAUNCH_TIMEOUT: float = 15
QUIT_TIMEOUT: float = 10

# Modifier names people type, by the keyboard table's name.
_MODIFIERS = {
    "cmd": "command",
    "command": "command",
    "shift": "shift",
    "alt": "option",
    "option": "option",
    "ctrl": "ctrl",
    "control": "ctrl",
}


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


def menu(app: str, path: str) -> None:
    """Press the menu item `path` names, such as "File > Save…", without taking focus.

    Three dots match an ellipsis.

    Raises:
        UsageError: `path` doesn't name a menu and an item.
        NoWindowError: `app` isn't running.
        ActionError: A step isn't in its menu, or the item is disabled.
    """
    steps = [_menu_title(step.strip()) for step in path.split(">")]
    if len(steps) < 2 or not all(steps):
        raise UsageError('Name a menu and an item, such as "File > Save…"')
    root = app_element(app)
    if root is None:
        raise NoWindowError(f"{app} isn't running")
    bar = next((c for c in _children(root) if c.get_ax_attribute("AXRole") == "AXMenuBar"), None)
    if bar is None:
        raise ActionError(f"{app} has no menu bar")
    choices, where = _children(bar), "the menu bar"
    for depth, step in enumerate(steps):
        match = next((c for c in choices if _menu_title(_title(c)) == step), None)
        if match is None:
            titles = ", ".join(t for t in (_title(c) for c in choices) if t)
            raise ActionError(f'No "{step}" in {where}. It has: {titles}')
        if depth == len(steps) - 1:
            if not match.get_ax_attribute("AXEnabled"):
                raise ActionError(f"{_title(match)} is disabled")
            match.press()
            return
        menus = [c for c in _children(match) if c.get_ax_attribute("AXRole") == "AXMenu"]
        choices, where = (_children(menus[0]) if menus else []), _title(match)


def _children(element: Any) -> list[Any]:
    return element.get_ax_attribute("AXChildren") or []


def _title(element: Any) -> str:
    return element.get_ax_attribute("AXTitle") or ""


def _menu_title(title: str) -> str:
    return title.replace("...", "…")


def parse_keys(combo: str) -> list[str]:
    """Return the key names of a shortcut such as "cmd+shift+s", modifiers first.

    Raises:
        UsageError: A name is empty or unknown, or a modifier comes last.
    """
    names = [name.strip() for name in combo.split("+")]
    *modifiers, key = [name if len(name) == 1 else name.lower() for name in names]
    key = key.lower()
    unknown = [m for m in modifiers if m.lower() not in _MODIFIERS]
    if unknown:
        raise UsageError(f'Unknown modifier "{unknown[0]}". Use cmd, shift, alt, or ctrl')
    if key not in KEYBOARD_KEYS or key in _MODIFIERS:
        raise UsageError(
            f'Unknown key "{key}". Use one character, or a name such as return, escape, tab,'
            " space, delete, up, or f5"
        )
    return [_MODIFIERS[m.lower()] for m in modifiers] + [key]


def keys(app: str, combo: str) -> None:
    """Bring `app` to the front and post the shortcut `combo`, such as "cmd+s".

    Raises:
        UsageError: `combo` isn't a shortcut.
        NoWindowError: `app` has no window.
        FocusError: `app` isn't in front, so nothing was posted.
    """
    names = parse_keys(combo)
    in_front = bring_to_front(app)
    if not in_front():
        raise FocusError(f"{app} left the front, so no keys were posted")
    keyboard.hotkey(*names)


def type_text(app: str, text: str) -> None:
    """Bring `app` to the front and type `text` into its focused element.

    Focus is checked before each character, so typing stops when `app` leaves the front.

    Raises:
        UsageError: `text` is empty.
        NoWindowError: `app` has no window.
        FocusError: `app` left the front, so typing stopped.
    """
    if not text:
        raise UsageError("type needs text")
    in_front = bring_to_front(app)
    for typed, character in enumerate(text):
        if not in_front():
            raise FocusError(
                f"Stopped after {typed} of {len(text)} characters: {app} left the front"
            )
        keyboard.write(character)


def screenshot(app: str, out: Optional[Path] = None, window: Optional[AXQuery] = None) -> Path:
    """Write a PNG of `app`'s front standard window, or the one `window` matches, and return it.

    `out` defaults to a new temp file. The PNG records its scale, like `capture`'s.

    Raises:
        NoWindowError: `app` has no matching window.
        PermissionError: Screen Recording isn't granted.
    """
    target = standard_window(app, window)
    frame = None if target is None else frame_of(target)
    if target is None or frame is None:
        raise NoWindowError(f"{app} has no matching window")
    number = window_number(target.pid, frame)
    if number is None:
        raise NoWindowError(f"Can't find {app}'s window on the window server")
    image = monitor.capture_window(number)
    width, height = Quartz.CGImageGetWidth(image), Quartz.CGImageGetHeight(image)
    if out is None:
        handle, name = tempfile.mkstemp(prefix=f"macuitest-{snake_case(app)}-", suffix=".png")
        os.close(handle)
        out = Path(name)
    write_png(image, (0, 0, width, height), out, width / (frame.x2 - frame.x1))
    return out


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
