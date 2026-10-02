"""Capture an app window's elements as PNGs and a generated `Screen` module."""

import json
import keyword
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from typing import Optional
from typing import Sequence

import Quartz
from Foundation import NSURL

from macuitest.config.constants import Region
from macuitest.lib.elements.locators.accessibility import GONE
from macuitest.lib.elements.locators.accessibility import AXQuery
from macuitest.lib.elements.locators.accessibility import frame_of
from macuitest.lib.elements.locators.accessibility import standard_window
from macuitest.lib.elements.locators.screen import image_folder
from macuitest.lib.elements.locators.screen import snake_case
from macuitest.lib.elements.ui.monitor import monitor

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
_CHROME = frozenset({"AXCloseButton", "AXFullScreenButton", "AXMinimizeButton", "AXZoomButton"})


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


def walk(window: Any) -> list[Found]:
    """Return every element under `window` with a frame, depth first, skipping window buttons."""
    found: list[Found] = []

    def visit(element: Any) -> None:
        for child in _read(element, "AXChildren") or []:
            if _read(child, "AXSubrole") in _CHROME:
                continue
            try:
                frame = frame_of(child)
            except GONE:
                frame = None
            if frame is not None:
                found.append(
                    Found(
                        role=_read(child, "AXRole") or "AXUnknown",
                        frame=frame,
                        identifier=_label(child, "AXIdentifier"),
                        description=_label(child, "AXDescription"),
                        title=_label(child, "AXTitle"),
                    )
                )
            visit(child)

    visit(window)
    return found


def window_number(pid: int, frame: Region) -> Optional[int]:
    """Return the window server number of process `pid`'s app window at `frame`, or None."""
    wanted = tuple(round(v) for v in (frame.x1, frame.y1, frame.x2 - frame.x1, frame.y2 - frame.y1))
    infos = Quartz.CGWindowListCopyWindowInfo(Quartz.kCGWindowListOptionAll, Quartz.kCGNullWindowID)
    for info in infos or []:
        bounds = info.get("kCGWindowBounds") or {}
        actual = tuple(round(bounds.get(key, -1)) for key in ("X", "Y", "Width", "Height"))
        if (
            info.get("kCGWindowOwnerPID") == pid
            and info.get("kCGWindowLayer") == 0
            and actual == wanted
        ):
            return int(info["kCGWindowNumber"])
    return None


def write_png(image: Any, box: tuple[int, int, int, int], path: Path) -> None:
    """Write the `box` (x, y, width, height) pixels of CGImage `image` to `path` as a PNG.

    Raises:
        OSError: The PNG can't be written.
    """
    cropped = Quartz.CGImageCreateWithImageInRect(image, Quartz.CGRectMake(*box))
    destination = Quartz.CGImageDestinationCreateWithURL(
        NSURL.fileURLWithPath_(str(path)), "public.png", 1, None
    )
    if destination is None:
        raise OSError(f"Can't write {path}")
    Quartz.CGImageDestinationAddImage(destination, cropped, None)
    if not Quartz.CGImageDestinationFinalize(destination):
        raise OSError(f"Can't write {path}")


def capture(
    app: str,
    out: Path,
    roles: Sequence[str] = (),
    margin: float = 4,
    force: bool = False,
    window: Optional[AXQuery] = None,
) -> list[Path]:
    """Write a PNG per element of one of `app`'s windows and a `Screen` module at `out`.

    The window is the first matching `window`, else the first standard window. Elements outside
    it are skipped, and `roles` keeps only those AX roles. Each PNG is the element's frame plus
    `margin` points, clipped to the window. Nothing is written when any target exists, unless
    `force` is set.

    Returns:
        The module path, then every PNG path.

    Raises:
        ValueError: `margin` is negative.
        LookupError: The app has no matching window, or no element is left after filtering.
        FileExistsError: A target exists and `force` isn't set.
        PermissionError: Accessibility or Screen Recording isn't granted.
    """
    if margin < 0:
        raise ValueError(f"The margin must be 0 or more, not {margin}")
    target = standard_window(app, window)
    window_frame = None if target is None else frame_of(target)
    if target is None or window_frame is None:
        raise LookupError(f"{app} has no matching window. Open it, then capture again.")
    walked = walk(target)
    inside = [f for f in walked if crop_box(f.frame, window_frame, 0, 1) is not None]
    kept = [f for f in inside if not roles or f.role in roles]
    if not kept:
        wanted = f" with role {', '.join(roles)}" if roles else ""
        raise LookupError(f"No elements{wanted} in {app}'s window")
    entries = plan(kept, walked)
    screen = class_name(target.get_ax_attribute("AXTitle"), app)
    folder = image_folder(out, screen)
    pngs = [folder / f"{entry.name}.png" for entry in entries]
    existing = [path for path in (out, *pngs) if path.exists()]
    if existing and not force:
        raise FileExistsError(
            f"{len(existing)} files exist, such as {existing[0]}. Pass --force to replace them."
        )
    number = window_number(target.pid, window_frame)
    if number is None:
        raise LookupError(f"Can't find {app}'s window on the window server")
    image = monitor.capture_window(number)
    scale = Quartz.CGImageGetWidth(image) / (window_frame.x2 - window_frame.x1)
    folder.mkdir(parents=True, exist_ok=True)
    for entry, png in zip(entries, pngs, strict=True):
        box = crop_box(entry.found.frame, window_frame, margin, scale)
        if box is not None:
            write_png(image, box, png)
    out.write_text(render_module(screen, app, entries, window))
    return [out, *pngs]


def _read(element: Any, name: str) -> Any:
    """Return attribute `name` of `element`, or None when reading it fails."""
    try:
        return element.get_ax_attribute(name)
    except GONE:
        return None


def _label(element: Any, name: str) -> Optional[str]:
    value = _read(element, name)
    return value if isinstance(value, str) and value.strip() else None


def _literal(value: str) -> str:
    # JSON strings are valid Python string literals, double-quoted like the rest of the repo.
    return json.dumps(value, ensure_ascii=False)
