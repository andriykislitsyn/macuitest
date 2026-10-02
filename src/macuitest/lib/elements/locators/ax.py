"""Find accessibility elements in running apps' windows."""

from dataclasses import dataclass
from typing import Any
from typing import Iterable
from typing import Iterator
from typing import Optional

from macuitest.config.constants import Region
from macuitest.lib.elements.native.native_ui_element import NativeUIElement
from macuitest.lib.operating_system.permissions import require_accessibility


@dataclass(frozen=True)
class AXQuery:
    """Accessibility attribute values an element must all have, as (attribute, value) pairs."""

    attributes: tuple[tuple[str, str], ...]

    @classmethod
    def of(
        cls,
        identifier: Optional[str] = None,
        description: Optional[str] = None,
        title: Optional[str] = None,
        role: Optional[str] = None,
    ) -> "AXQuery":
        """Return a query for the given `AXIdentifier`, `AXDescription`, `AXTitle`, and `AXRole`.

        Raises:
            TypeError: Every value is None.
        """
        given = {
            "AXIdentifier": identifier,
            "AXDescription": description,
            "AXTitle": title,
            "AXRole": role,
        }
        attributes = tuple((name, value) for name, value in given.items() if value is not None)
        if not attributes:
            raise TypeError("Pass at least one of identifier, description, title, or role")
        return cls(attributes)

    def matches(self, element: Any) -> bool:
        """Return whether `element` has every attribute value of this query."""
        return all(element.get_ax_attribute(name) == value for name, value in self.attributes)

    def __str__(self) -> str:
        return ", ".join(f"{name}={value!r}" for name, value in self.attributes)


def find_first(roots: Iterable[Any], query: AXQuery) -> Optional[Any]:
    """Return the first descendant of `roots`, depth first, that matches `query`, or None."""
    for root in roots:
        for element in _descendants(root):
            if query.matches(element):
                return element
    return None


def app_root(app: str) -> Optional[NativeUIElement]:
    """Return the accessibility element of running app `app`, or None if it isn't running.

    Raises:
        PermissionError: Accessibility isn't granted.
    """
    require_accessibility()
    try:
        return NativeUIElement.from_localized_name(app)
    except ValueError:
        return None


def windows(app: str) -> list[Any]:
    """Return `app`'s windows, front to back, or an empty list if it isn't running."""
    root = app_root(app)
    return [] if root is None else list(root.get_ax_attribute("AXWindows") or [])


def standard_window(app: str) -> Optional[Any]:
    """Return `app`'s first standard window that isn't minimized, or None."""
    for window in windows(app):
        if window.get_ax_attribute("AXSubrole") == "AXStandardWindow" and not (
            window.get_ax_attribute("AXMinimized")
        ):
            return window
    return None


def standard_window_frame(app: str) -> Optional[Region]:
    """Return the frame of `app`'s first standard window that isn't minimized, or None."""
    window = standard_window(app)
    return None if window is None else frame_of(window)


def frame_of(element: Any) -> Optional[Region]:
    """Return `element`'s frame in global points, or None when it has no area."""
    position = element.get_ax_attribute("AXPosition")
    size = element.get_ax_attribute("AXSize")
    if not position or not size or size[0] <= 0 or size[1] <= 0:
        return None
    (x, y), (width, height) = position, size
    return Region(x, y, x + width, y + height)


def _descendants(element: Any) -> Iterator[Any]:
    for child in element.get_ax_attribute("AXChildren") or []:
        yield child
        yield from _descendants(child)
