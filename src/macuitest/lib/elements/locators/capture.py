"""Capture an app window's elements as PNGs and a generated `Screen` module."""

import ast
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

from macuitest.config.constants import POINTS_PER_INCH
from macuitest.config.constants import Region
from macuitest.lib.core import wait_condition
from macuitest.lib.elements.locators.accessibility import GONE
from macuitest.lib.elements.locators.accessibility import AXQuery
from macuitest.lib.elements.locators.accessibility import app_root
from macuitest.lib.elements.locators.accessibility import frame_of
from macuitest.lib.elements.locators.accessibility import standard_window
from macuitest.lib.elements.locators.accessibility import windows
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
# Most stable first. Every key must be set for a locator to apply.
_LOCATOR_KEYS = (("identifier",), ("description", "role"), ("title", "role"))
# Names that would shadow `Screen` attributes, or the factories inside the generated class body.
_RESERVED = frozenset({"app", "window", "applescript", "ax", "image", "text"})
# `window()` keywords by the AX attribute an `AXQuery` stores.
_WINDOW_KEYWORDS = {"AXTitle": "title", "AXSubrole": "subrole"}
# Seconds to wait for the window after activating the app.
WINDOW_TIMEOUT = 2
# Roles whose contents are data, such as a list of fonts.
_COLLECTIONS = frozenset({"AXList", "AXOutline", "AXTable"})
_CHROME = frozenset({"AXCloseButton", "AXFullScreenButton", "AXMinimizeButton", "AXZoomButton"})
# AppKit generates identifiers such as `_NS:34`, which change between launches.
_GENERATED_IDENTIFIER = re.compile(r"_NS:\d+")


@dataclass(frozen=True, eq=False)
class Found:
    """An element seen while walking a window. `chrome` marks window buttons and their parts.

    `in_collection` marks everything inside a table, outline, or list.

    `role` is None when it can't be read. `depth` is 1 for the window's children, 2 for theirs,
    and so on.
    """

    role: Optional[str]
    frame: Optional[Region]
    identifier: Optional[str] = None
    description: Optional[str] = None
    title: Optional[str] = None
    chrome: bool = False
    in_collection: bool = False
    depth: int = 1
    value: Any = None


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
    kind = KINDS.get(found.role or "")
    for keys in _LOCATOR_KEYS:
        values = {key: getattr(found, key) for key in keys}
        if not all(values.values()):
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
    role = snake_case((found.role or "").removeprefix("AX")) or "element"
    labels = (found.identifier, found.description, found.title)
    base = next((name for name in (snake_case(label or "") for label in labels) if name), role)
    if base[0].isdigit():
        base = f"{role}_{base}"
    if keyword.iskeyword(base) or base in _RESERVED:
        base += "_"
    name, suffix = base, 2
    while name in taken:
        name, suffix = f"{base.rstrip('_')}_{suffix}", suffix + 1
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
        if name and not name[0].isdigit() and not keyword.iskeyword(name):
            return name
    return "AppScreen"


def render_module(
    screen: str,
    app: str,
    entries: list[Entry],
    window: Optional[AXQuery] = None,
    skipped: int = 0,
) -> str:
    """Return the source of a module declaring `screen` for `app` with `entries`.

    `window` is the query of a window screen, rendered as `window=window(...)`. `skipped` counts
    the elements left out from inside tables and lists, noted in a comment.
    """
    lines = [
        f'"""Generated by `python -m macuitest.locators capture {_literal(app)}`. Edit freely."""',
        "",
        *(f"from {module} import {name}" for module, name in _imports(entries, window)),
        "",
        "",
        *_class_lines(screen, app, entries, window, skipped),
    ]
    return "\n".join(lines) + "\n"


def append_screen(
    source: str,
    screen: str,
    app: str,
    entries: list[Entry],
    window: Optional[AXQuery] = None,
    skipped: int = 0,
) -> str:
    """Return module `source` with `screen` appended, like `render_module` declares it.

    Adds the imports `source` doesn't bind yet, after its last top-level import.
    """
    body = ast.parse(source).body
    imports = [node for node in body if isinstance(node, (ast.Import, ast.ImportFrom))]
    bound = {alias.asname or alias.name for node in imports for alias in node.names}
    missing = [
        f"from {module} import {name}\n"
        for module, name in _imports(entries, window)
        if name not in bound
    ]
    lines = source.splitlines(keepends=True)
    if imports:
        anchor = imports[-1].end_lineno or 0
    else:
        docstring = ast.get_docstring(ast.Module(body=body[:1], type_ignores=[]))
        anchor = (body[0].end_lineno or 0) if docstring is not None else 0
        missing.append("\n")
    lines[anchor:anchor] = missing
    head = "".join(lines).rstrip("\n")
    return "\n".join([head, "", "", *_class_lines(screen, app, entries, window, skipped)]) + "\n"


def defines(source: str, name: str) -> bool:
    """Return whether module `source` declares a top-level class `name`."""
    return any(
        isinstance(node, ast.ClassDef) and node.name == name for node in ast.parse(source).body
    )


def _imports(entries: list[Entry], window: Optional[AXQuery]) -> list[tuple[str, str]]:
    """Return the (module, name) imports a screen of `entries` needs."""
    names = {entry.locator.split("(")[0] for entry in entries}
    if window is not None:
        names.add("window")
    kinds = sorted({entry.kind for entry in entries if entry.kind})
    return [
        ("macuitest.lib.elements.locators", "Screen"),
        *(("macuitest.lib.elements.locators", name) for name in sorted(names)),
        *(("macuitest.lib.elements.native_element", kind) for kind in kinds),
    ]


def _class_lines(
    screen: str, app: str, entries: list[Entry], window: Optional[AXQuery], skipped: int
) -> list[str]:
    header = f"app={_literal(app)}"
    if window is not None:
        arguments = (f"{_WINDOW_KEYWORDS[key]}={_literal(v)}" for key, v in window.attributes)
        header += f", window=window({', '.join(arguments)})"
    note = []
    if skipped:
        note = [
            f"    # Skipped {skipped} elements inside tables and lists without a stable locator.",
            '    # Their contents change, so find a row by what it shows, such as text("...").',
        ]
    body = [f"    {entry.name} = {entry.locator}" for entry in entries] or ["    pass"]
    return [f"class {screen}(Screen, {header}):", *note, *body]


def walk(window: Any) -> list[Found]:
    """Return every element under `window`, depth first, in the order `ax()` searches them.

    Elements without a frame are included, since `ax()` can still match them.
    """
    found: list[Found] = []

    def visit(element: Any, in_chrome: bool, in_collection: bool, depth: int) -> None:
        in_collection = in_collection or _read(element, "AXRole") in _COLLECTIONS
        for child in _read(element, "AXChildren") or []:
            chrome = in_chrome or _read(child, "AXSubrole") in _CHROME
            try:
                frame = frame_of(child)
            except GONE:
                frame = None
            found.append(
                Found(
                    role=_read(child, "AXRole"),
                    frame=frame,
                    identifier=_identifier(child),
                    description=_label(child, "AXDescription"),
                    title=_label(child, "AXTitle"),
                    chrome=chrome,
                    in_collection=in_collection,
                    depth=depth,
                    value=_read(child, "AXValue"),
                )
            )
            visit(child, chrome, in_collection, depth + 1)

    visit(window, False, False, 1)
    return found


def window_number(pid: int, frame: Region) -> Optional[int]:
    """Return the window server number of process `pid`'s window at `frame`, or None.

    App windows at layer 0 win over floating panels above it, then on-screen windows win.
    """
    wanted = tuple(round(v) for v in (frame.x1, frame.y1, frame.x2 - frame.x1, frame.y2 - frame.y1))
    infos = Quartz.CGWindowListCopyWindowInfo(Quartz.kCGWindowListOptionAll, Quartz.kCGNullWindowID)
    matches = [
        info
        for info in infos or []
        if info.get("kCGWindowOwnerPID") == pid
        and tuple(
            round((info.get("kCGWindowBounds") or {}).get(key, -1))
            for key in ("X", "Y", "Width", "Height")
        )
        == wanted
    ]
    # Inactive native tabs are off-screen windows with the same bounds as the visible one.
    matches.sort(
        key=lambda info: (info.get("kCGWindowLayer") != 0, not info.get("kCGWindowIsOnscreen"))
    )
    return int(matches[0]["kCGWindowNumber"]) if matches else None


def write_png(image: Any, box: tuple[int, int, int, int], path: Path, scale: float) -> None:
    """Write the `box` (x, y, width, height) pixels of CGImage `image` to `path` as a PNG.

    The PNG records `scale`, the image's pixels per point, as its DPI.

    Raises:
        OSError: The PNG can't be written.
    """
    cropped = Quartz.CGImageCreateWithImageInRect(image, Quartz.CGRectMake(*box))
    destination = Quartz.CGImageDestinationCreateWithURL(
        NSURL.fileURLWithPath_(str(path)), "public.png", 1, None
    )
    if destination is None:
        raise OSError(f"Can't write {path}")
    dpi = POINTS_PER_INCH * scale
    Quartz.CGImageDestinationAddImage(
        destination,
        cropped,
        {Quartz.kCGImagePropertyDPIWidth: dpi, Quartz.kCGImagePropertyDPIHeight: dpi},
    )
    if not Quartz.CGImageDestinationFinalize(destination):
        raise OSError(f"Can't write {path}")


def capture(
    app: str,
    out: Path,
    roles: Sequence[str] = (),
    margin: float = 4,
    force: bool = False,
    window: Optional[AXQuery] = None,
    append: bool = False,
) -> list[Path]:
    """Write a PNG per element of one of `app`'s windows and a `Screen` module at `out`.

    Activates the app first, since floating panels, and some apps' windows, appear in the
    accessibility tree only while the app is active. The window is the first matching
    `window`, else the first standard window. Elements outside
    it are skipped, and `roles` keeps only those AX roles. Each PNG is the element's frame plus
    `margin` points, clipped to the window. The screen class is named after the window for a
    `window` screen, else after the app. Without `roles`, elements inside tables and lists are
    skipped unless they have an `ax()` locator. Nothing is written when any target exists, unless
    `force` is set. With `append`, the screen is added to an existing module at `out` instead.

    Returns:
        The module path, then every PNG path.

    Raises:
        ValueError: `margin` is negative.
        LookupError: The app has no matching window, or no element is left after filtering.
        FileExistsError: A target exists and `force` isn't set, or the module to append to
            already defines the screen.
        PermissionError: Accessibility or Screen Recording isn't granted.
    """
    if margin < 0:
        raise ValueError(f"The margin must be 0 or more, not {margin}")
    root = app_root(app)
    try:
        if root is not None:
            # Floating panels, and some apps' windows, appear in AX only while the app is active.
            root.activate()
    except GONE:
        pass
    found = wait_condition(lambda: standard_window(app, window), timeout=WINDOW_TIMEOUT)
    target = found or None
    window_frame = None if target is None else frame_of(target)
    if target is None or window_frame is None:
        raise LookupError(f"{app} has no matching window. Open it, then capture again.")
    own = walk(target)
    # A screen without window= searches every window front to back, so earlier ones count too.
    walked = [*(_windows_before(app, target) if window is None else []), *own]
    inside = [
        f
        for f in own
        if not f.chrome and f.frame is not None and crop_box(f.frame, window_frame, 0, 1)
    ]
    kept = [f for f in inside if not roles or f.role in roles]
    if not kept:
        wanted = f" with role {', '.join(roles)}" if roles else ""
        raise LookupError(f"No elements{wanted} in {app}'s window")
    entries = plan(kept, walked)
    skipped = 0
    if not roles:
        # A table's rows show data that changes, so a screenshot of each is noise.
        folded = {id(e) for e in entries if e.found.in_collection and e.locator == "image()"}
        entries = [entry for entry in entries if id(entry) not in folded]
        skipped = len(folded)
    # A standard window's title is often a document name, which changes between runs.
    title = None if window is None else target.get_ax_attribute("AXTitle")
    screen = class_name(title, app)
    folder = image_folder(out, screen)
    pngs = [folder / f"{entry.name}.png" for entry in entries]
    source = out.read_text() if append and out.exists() else None
    if source is not None and defines(source, screen):
        raise FileExistsError(f"{out} already defines {screen}")
    targets = pngs if source is not None else [out, *pngs]
    existing = [path for path in targets if path.exists()]
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
        frame = entry.found.frame
        box = None if frame is None else crop_box(frame, window_frame, margin, scale)
        if box is not None:
            write_png(image, box, png, scale)
    if source is None:
        out.write_text(render_module(screen, app, entries, window, skipped))
    else:
        out.write_text(append_screen(source, screen, app, entries, window, skipped))
    return [out, *pngs]


def _windows_before(app: str, target: Any) -> list[Found]:
    """Return the elements of `app`'s windows in front of `target`, in search order."""
    found: list[Found] = []
    key = _window_key(target)
    for window in windows(app):
        if _window_key(window) == key:
            break
        found += walk(window)
    return found


def _window_key(window: Any) -> tuple:
    try:
        return _read(window, "AXTitle"), frame_of(window)
    except GONE:
        return None, None


def _read(element: Any, name: str) -> Any:
    """Return attribute `name` of `element`, or None when reading it fails."""
    try:
        return element.get_ax_attribute(name)
    except GONE:
        return None


def _identifier(element: Any) -> Optional[str]:
    identifier = _label(element, "AXIdentifier")
    if identifier is None or _GENERATED_IDENTIFIER.fullmatch(identifier):
        return None
    return identifier


def _label(element: Any, name: str) -> Optional[str]:
    value = _read(element, name)
    return value if isinstance(value, str) and value.strip() else None


def _literal(value: str) -> str:
    # JSON strings are valid Python string literals, double-quoted like the rest of the repo.
    return json.dumps(value, ensure_ascii=False)
