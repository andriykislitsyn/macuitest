"""Act on one element: the verbs of the `macuitest` command, for any agent front end.

Functions return values and raise typed errors. They never print, so the command line and other
front ends format results their own way.
"""

import re
import time
from dataclasses import dataclass
from typing import Any
from typing import Optional

from macuitest.config.constants import Region
from macuitest.lib.core import wait_condition
from macuitest.lib.elements import applescript_element
from macuitest.lib.elements import native_element
from macuitest.lib.elements.controllers.mouse import mouse
from macuitest.lib.elements.locators.accessibility import GONE
from macuitest.lib.elements.locators.accessibility import app_root
from macuitest.lib.elements.locators.accessibility import frame_of
from macuitest.lib.elements.screen_element import ScreenElement

# Seconds to wait for an activated app to come to the front before refusing to click.
FOCUS_TIMEOUT: float = 3
# Invisible direction marks, which apps such as Calculator put around displayed text.
_BIDI_MARKS = re.compile("[\u200e\u200f\u202a-\u202e\u2066-\u2069]")


class UsageError(ValueError):
    """The verb doesn't apply to this kind of element."""


class FocusError(RuntimeError):
    """The app didn't come to the front, so no input was sent."""


class ActionError(RuntimeError):
    """The element doesn't support the action."""


class NoWindowError(LookupError):
    """The app isn't running, or has no window to act in."""


@dataclass(frozen=True)
class Snapshot:
    """What `find` saw: the accessibility role, title, and value, and the box on screen."""

    role: Optional[str] = None
    title: Optional[str] = None
    value: Any = None
    box: Optional[Region] = None


def find(element: Any) -> Optional[Snapshot]:
    """Return what the element looks like now, or None when it isn't there. Doesn't wait."""
    if isinstance(element, ScreenElement):
        box = element.locate()
        return None if box is None else Snapshot(box=box)
    if isinstance(element, native_element.NativeElement):
        try:
            item = element.item
        except LookupError:
            return None
        read = item.get_ax_attribute
        value = _without_marks(read("AXValue"))
        return Snapshot(read("AXRole"), read("AXTitle"), value, frame_of(item))
    if not element.exists:
        return None
    return Snapshot(value=_without_marks(element.value))


def read(element: Any) -> Any:
    """Return the element's value, or an AppleScript text element's text, without direction marks.

    Raises:
        UsageError: The element is visible text or an image.
    """
    if isinstance(element, ScreenElement):
        raise UsageError("read needs an ax() or applescript() element")
    if isinstance(element, applescript_element.TextElement):
        return _without_marks(element.get_text())
    return _without_marks(element.value)


def _without_marks(value: Any) -> Any:
    return _BIDI_MARKS.sub("", value) if isinstance(value, str) else value


def wait(element: Any, vanish: bool = False, timeout: Optional[float] = None) -> bool:
    """Return whether the element appears, or vanishes with `vanish`, within `timeout` seconds.

    `timeout` defaults to the `settings.elements` timeouts.
    """
    if vanish:
        return bool(element.wait_vanish(timeout))
    return bool(element.wait_displayed(timeout))


def press(element: Any, pause: Optional[float] = None) -> None:
    """Perform the element's press action without moving the pointer, after `pause` seconds.

    Raises:
        UsageError: The element is visible text or an image.
        ActionError: The accessibility element doesn't offer a press action.
    """
    if isinstance(element, ScreenElement):
        raise UsageError("press needs an ax() or applescript() element. Use click for this one.")
    if isinstance(element, native_element.NativeElement):
        item = element.item
        # macOS reports success for a press the element doesn't support, and nothing happens.
        supported = item.ax_actions
        if "AXPress" not in supported:
            offered = ", ".join(supported) or "none"
            raise ActionError(f"The element has no press action (it offers: {offered}). Try click.")
        if pause:
            time.sleep(pause)
        item.press()
    elif pause is None:
        element.click()
    else:
        element.click(pause)


def set_value(element: Any, value: str) -> None:
    """Write `value` to the element, converted to a number when the current value is one.

    Raises:
        UsageError: The element is visible text or an image, or an AppleScript element that
            isn't a text element.
        ValueError: The current value is a number and `value` isn't.
    """
    if isinstance(element, native_element.NativeElement):
        current = element.value
        if isinstance(current, (int, float)) and not isinstance(current, bool):
            element.value = type(current)(value)
        else:
            element.value = value
    elif isinstance(element, applescript_element.TextElement):
        element.set_text(value)
    else:
        raise UsageError("set needs an ax() element, or an applescript() text element")


def click(element: Any, app: Optional[str], double: bool = False, right: bool = False) -> None:
    """Bring `app` to the front, find the element, then click its center with the mouse.

    Focus is checked again after the element is found, right before the click.

    Raises:
        UsageError: `app` is None, both `double` and `right` are set, or the element belongs to
            another process.
        NoWindowError: `app` has no window.
        LookupError: The element isn't there.
        FocusError: `app` isn't in front, so nothing was clicked.
    """
    if double and right:
        raise UsageError("Pass --double or --right, not both")
    if app is None:
        raise UsageError("click needs the element's app, to bring it to the front first")
    process = getattr(element, "process", app)
    if process != app:
        raise UsageError(f"The element belongs to {process}, not {app}")
    root = app_root(app)
    if root is None:
        raise NoWindowError(f"{app} has no window")
    try:
        root.activate()
    except GONE:
        pass
    in_front = lambda: root.get_ax_attribute("AXFrontmost")  # noqa: E731
    if not wait_condition(in_front, timeout=FOCUS_TIMEOUT):
        raise FocusError(f"{app} didn't come to the front, so nothing was clicked")
    # Found after activating, since another window may cover the element until then.
    center = element.get_center() if isinstance(element, ScreenElement) else element.frame.center
    # Finding a screen element can take seconds, enough for the user to switch apps.
    if not in_front():
        raise FocusError(f"{app} left the front, so nothing was clicked")
    if double:
        mouse.double_click(center.x, center.y)
    elif right:
        mouse.right_click(center.x, center.y)
    else:
        mouse.click(center.x, center.y)
