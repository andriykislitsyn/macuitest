"""Capture an app window's elements as PNGs and a generated `Screen` module."""

import json
import keyword
import re
from dataclasses import dataclass
from typing import Optional

from macuitest.config.constants import Region
from macuitest.lib.elements.locators.accessibility import AXQuery
from macuitest.lib.elements.locators.screen import snake_case

# `native_element` classes by role, so generated ax() entries get actions such as press.
KINDS = {
    "AXButton": "Button",
    "AXCell": "Cell",
    "AXCheckBox": "CheckBox",
    "AXDisclosureTriangle": "DisclosureTriangle",
    "AXImage": "Image",
    "AXLink": "Link",
    "AXMenuItem": "MenuItem",
    "AXRow": "Row",
    "AXStaticText": "StaticText",
    "AXTextField": "TextField",
    "AXWebArea": "WebView",
}
# Most stable first. The first key must be set for a locator to apply.
_LOCATOR_KEYS = (("identifier",), ("description", "role"), ("title", "role"))
# Names that would shadow `Screen` attributes.
_RESERVED = frozenset({"app", "window"})
# `window()` keywords by the AX attribute an `AXQuery` stores.
_WINDOW_KEYWORDS = {"AXTitle": "title", "AXSubrole": "subrole"}


@dataclass(frozen=True, eq=False)
class Found:
    """An element seen while walking a window."""

    role: str
    frame: Region
    identifier: Optional[str] = None
    description: Optional[str] = None
    title: Optional[str] = None


@dataclass(frozen=True)
class Entry:
    """One attribute of a generated screen."""

    name: str
    locator: str
    kind: Optional[str]
    found: Found


def locator_for(found: Found, walked: list[Found]) -> tuple[str, Optional[str]]:
    """Return the source of the most stable locator that resolves to `found`, and its kind.

    A locator resolves to `found` when `found` is the first element of `walked`, the whole window
    in depth-first order, that it matches. Without one, the element gets `image()`.
    """
    kind = KINDS.get(found.role)
    for keys in _LOCATOR_KEYS:
        values = {key: getattr(found, key) for key in keys}
        if not values[keys[0]]:
            continue
        first = next(
            (f for f in walked if all(getattr(f, key) == v for key, v in values.items())), None
        )
        if first is found:
            arguments = [f"{key}={_literal(v)}" for key, v in values.items()]
            if kind:
                arguments.append(f"kind={kind}")
            return f"ax({', '.join(arguments)})", kind
    return "image()", None


def attribute_name(found: Found, taken: set[str]) -> str:
    """Return a unique, valid attribute name for `found` and add it to `taken`."""
    role = snake_case(found.role.removeprefix("AX")) or "element"
    labels = (found.identifier, found.description, found.title)
    base = next((name for name in (snake_case(label or "") for label in labels) if name), role)
    if base[0].isdigit():
        base = f"{role}_{base}"
    if keyword.iskeyword(base) or base in _RESERVED:
        base += "_"
    name, suffix = base, 2
    while name in taken:
        name, suffix = f"{base}_{suffix}", suffix + 1
    taken.add(name)
    return name


def plan(kept: list[Found], walked: list[Found]) -> list[Entry]:
    """Return an entry for every element in `kept`, choosing locators against all of `walked`."""
    taken: set[str] = set()
    entries = []
    for found in kept:
        locator, kind = locator_for(found, walked)
        entries.append(Entry(attribute_name(found, taken), locator, kind, found))
    return entries


def crop_box(
    frame: Region, window: Region, margin: float, scale: float
) -> Optional[tuple[int, int, int, int]]:
    """Return `frame` plus `margin` points, clipped to `window`, as pixels in a window capture.

    The box is (x, y, width, height) from the capture's top left, at `scale` pixels per point.
    Returns None when nothing of `frame` lies inside `window`.
    """
    x1, y1 = max(frame.x1 - margin, window.x1), max(frame.y1 - margin, window.y1)
    x2, y2 = min(frame.x2 + margin, window.x2), min(frame.y2 + margin, window.y2)
    if x2 <= x1 or y2 <= y1:
        return None
    left, top = round((x1 - window.x1) * scale), round((y1 - window.y1) * scale)
    right, bottom = round((x2 - window.x1) * scale), round((y2 - window.y1) * scale)
    return left, top, right - left, bottom - top


def class_name(title: Optional[str], app: str) -> str:
    """Return a PascalCase class name from the window `title`, else from `app`."""
    for source in (title or "", app):
        name = "".join(word[:1].upper() + word[1:] for word in re.findall(r"[0-9A-Za-z]+", source))
        if name and not name[0].isdigit():
            return name
    return "AppScreen"


def render_module(
    screen: str, app: str, entries: list[Entry], window: Optional[AXQuery] = None
) -> str:
    """Return the source of a module declaring `screen` for `app` with `entries`.

    `window` is the query of a window screen, rendered as `window=window(...)`.
    """
    names = {entry.locator.split("(")[0] for entry in entries}
    header = f"app={_literal(app)}"
    if window is not None:
        names.add("window")
        arguments = (f"{_WINDOW_KEYWORDS[key]}={_literal(v)}" for key, v in window.attributes)
        header += f", window=window({', '.join(arguments)})"
    kinds = sorted({entry.kind for entry in entries if entry.kind})
    lines = [
        f'"""Generated by `python -m macuitest.locators capture {_literal(app)}`. Edit freely."""',
        "",
        "from macuitest.lib.elements.locators import Screen",
        *(f"from macuitest.lib.elements.locators import {name}" for name in sorted(names)),
        *(f"from macuitest.lib.elements.native_element import {kind}" for kind in kinds),
        "",
        "",
        f"class {screen}(Screen, {header}):",
        *([f"    {entry.name} = {entry.locator}" for entry in entries] or ["    pass"]),
    ]
    return "\n".join(lines) + "\n"


def _literal(value: str) -> str:
    # JSON strings are valid Python string literals, double-quoted like the rest of the repo.
    return json.dumps(value, ensure_ascii=False)
