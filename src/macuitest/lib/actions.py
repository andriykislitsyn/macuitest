"""Act on one element: the verbs of the `macuitest` command, for any agent front end.

Functions return values and raise typed errors. They never print, so the command line and other
front ends format results their own way.
"""

from dataclasses import dataclass
from typing import Any
from typing import Optional

from macuitest.config.constants import Region
from macuitest.lib.elements import applescript_element
from macuitest.lib.elements import native_element
from macuitest.lib.elements.locators.accessibility import frame_of
from macuitest.lib.elements.screen_element import ScreenElement


class UsageError(ValueError):
    """The verb doesn't apply to this kind of element."""


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
        return Snapshot(read("AXRole"), read("AXTitle"), read("AXValue"), frame_of(item))
    if not element.exists:
        return None
    return Snapshot(value=element.value)


def read(element: Any) -> Any:
    """Return a text element's text, else the element's value.

    Raises:
        UsageError: The element is visible text or an image.
    """
    if isinstance(element, ScreenElement):
        raise UsageError("read needs an ax() or applescript() element")
    if isinstance(element, native_element.StaticText):
        return element.text
    if isinstance(element, applescript_element.TextElement):
        return element.get_text()
    return element.value


def wait(element: Any, vanish: bool = False, timeout: Optional[float] = None) -> bool:
    """Return whether the element appears, or vanishes with `vanish`, within `timeout` seconds.

    `timeout` defaults to the `settings.elements` timeouts.
    """
    if vanish:
        return bool(element.wait_vanish(timeout))
    return bool(element.wait_displayed(timeout))
