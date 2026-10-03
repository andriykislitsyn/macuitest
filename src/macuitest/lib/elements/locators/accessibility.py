"""Find accessibility elements in running apps' windows."""

import os
from dataclasses import dataclass
from typing import Any
from typing import Iterable
from typing import Iterator
from typing import Optional

import Quartz

from macuitest.config.constants import Region
from macuitest.lib.elements.native.calls import AXErrorCannotComplete
from macuitest.lib.elements.native.calls import AXErrorFailure
from macuitest.lib.elements.native.calls import AXErrorIllegalArgument
from macuitest.lib.elements.native.calls import AXErrorInvalidUIElement
from macuitest.lib.elements.native.native_ui_element import NativeUIElement
from macuitest.lib.operating_system.permissions import require_accessibility

# Raised for an app that is quitting or not answering yet, for an element that just vanished,
# and by SwiftUI for some attributes of otherwise readable elements (AXErrorFailure).
GONE = (AXErrorCannotComplete, AXErrorFailure, AXErrorIllegalArgument, AXErrorInvalidUIElement)
# How deep lookups and walks descend. Real UIs nest a few dozen levels at most.
MAX_DEPTH = 100
# Process IDs by app name. Finding a running app through NSWorkspace spins the run loop for 1 s.
_pids: dict[str, int] = {}


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
        subrole: Optional[str] = None,
    ) -> "AXQuery":
        """Return a query matching the given accessibility attribute values.

        The keywords map to `AXIdentifier`, `AXDescription`, `AXTitle`, `AXRole`, and `AXSubrole`.

        Raises:
            TypeError: Every value is None.
        """
        given = {
            "AXIdentifier": identifier,
            "AXDescription": description,
            "AXTitle": title,
            "AXRole": role,
            "AXSubrole": subrole,
        }
        attributes = tuple((name, value) for name, value in given.items() if value is not None)
        if not attributes:
            raise TypeError("Pass at least one attribute to match, such as identifier or title")
        return cls(attributes)

    def matches(self, element: Any) -> bool:
        """Return whether `element` has every attribute value of this query."""
        return all(element.get_ax_attribute(name) == value for name, value in self.attributes)

    def __str__(self) -> str:
        return ", ".join(f"{name}={value!r}" for name, value in self.attributes)


def find_first(roots: Iterable[Any], query: AXQuery) -> Optional[Any]:
    """Return the first descendant of `roots`, depth first, that matches `query`, or None.

    Elements that vanish during the search are skipped.
    """
    path = find_path(roots, query)
    return None if path is None else path[-1]


def find_path(
    roots: Iterable[Any], query: AXQuery, above: tuple[Any, ...] = ()
) -> Optional[tuple[Any, ...]]:
    """Return the path from a root to the first descendant that matches `query`, or None.

    `above` is the path to the roots' parent when the roots came from an earlier search, so a
    nested search skips the same loops and stops at the same depth as one from the window.
    """
    for root in roots:
        for path in _descendants(root, above):
            try:
                if query.matches(path[-1]):
                    return path
            except GONE:
                continue
    return None


def app_root(app: str) -> Optional[NativeUIElement]:
    """Return the accessibility element of app `app`, or None if it has no window.

    Raises:
        PermissionError: Accessibility isn't granted.
    """
    require_accessibility()
    pid = _pids.get(app)
    if pid is None or not _alive(pid):
        pid = _window_owner(app)
        if pid is None:
            _pids.pop(app, None)
            return None
        _pids[app] = pid
    return NativeUIElement.from_pid(pid)


def windows(app: str) -> list[Any]:
    """Return `app`'s windows, front to back, or an empty list if it has none or isn't answering."""
    root = app_root(app)
    return [] if root is None else _windows(root)


def standard_window(app: str, query: Optional[AXQuery] = None) -> Optional[Any]:
    """Return `app`'s first window matching `query` that isn't minimized, or None.

    Without `query`, that is the first standard window. A hidden app has none, since its windows
    aren't on screen.
    """
    root = app_root(app)
    try:
        if root is None or root.get_ax_attribute("AXHidden"):
            return None
    except GONE:
        return None
    for window in _windows(root):
        try:
            if query is None:
                wanted = window.get_ax_attribute("AXSubrole") == "AXStandardWindow"
            else:
                wanted = query.matches(window)
            if wanted and not window.get_ax_attribute("AXMinimized"):
                return window
        except GONE:
            continue
    return None


def standard_window_frame(app: str, query: Optional[AXQuery] = None) -> Optional[Region]:
    """Return the frame of `standard_window(app, query)`, or None."""
    window = standard_window(app, query)
    try:
        return None if window is None else frame_of(window)
    except GONE:
        return None


def frame_of(element: Any) -> Optional[Region]:
    """Return `element`'s frame in global points, or None when it has no area."""
    position = element.get_ax_attribute("AXPosition")
    size = element.get_ax_attribute("AXSize")
    if not position or not size or size[0] <= 0 or size[1] <= 0:
        return None
    (x, y), (width, height) = position, size
    return Region(x, y, x + width, y + height)


def _windows(root: Any) -> list[Any]:
    try:
        return list(root.get_ax_attribute("AXWindows") or [])
    except GONE:
        return []


def _window_owner(app: str) -> Optional[int]:
    """Return the process ID owning a window of app `app`, from the live window server list."""
    infos = Quartz.CGWindowListCopyWindowInfo(Quartz.kCGWindowListOptionAll, Quartz.kCGNullWindowID)
    for info in infos or []:
        if info.get("kCGWindowOwnerName") == app and info.get("kCGWindowLayer") == 0:
            return int(info["kCGWindowOwnerPID"])
    return None


def _alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def identity(element: Any) -> Any:
    """Return what tells accessibility elements apart: the AX reference, else the object."""
    return getattr(element, "ref", element)


def _descendants(element: Any, above: tuple[Any, ...] = ()) -> Iterator[tuple[Any, ...]]:
    """Yield the path to each descendant of `element`, depth first. `above` leads to `element`."""
    path = (*above, element)
    if len(path) > MAX_DEPTH:
        return
    try:
        children = element.get_ax_attribute("AXChildren") or []
    except GONE:
        return
    ancestors = [identity(ancestor) for ancestor in path]
    for child in children:
        # Some apps list an ancestor among an element's children, which would loop forever.
        if identity(child) in ancestors:
            continue
        yield (*path, child)
        yield from _descendants(child, path)
