"""Turn a command line target, a locator string or a `Screen` attribute, into an element."""

import ast
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from typing import Callable
from typing import Optional
from typing import Sequence

from macuitest.lib.elements import native_element
from macuitest.lib.elements.locators.accessibility import AXQuery
from macuitest.lib.elements.locators.check import load_module
from macuitest.lib.elements.locators.factories import AXLocator
from macuitest.lib.elements.locators.factories import ax
from macuitest.lib.elements.locators.factories import text
from macuitest.lib.elements.locators.screen import Locator
from macuitest.lib.elements.locators.screen import Screen

_FACTORIES: dict[str, Callable[..., Locator]] = {"ax": ax, "text": text}
# Factories a locator string can't use, with the reason.
_MODULE_ONLY = {
    # Its PNG path comes from the module that declares the screen.
    "image": "image() needs a Screen module",
    # Its locator runs as AppleScript, which can run shell commands.
    "applescript": "applescript() runs as AppleScript, so it works only in a Screen module",
}
# `kind=` names for ax().
_KINDS = {
    name: value
    for name, value in vars(native_element).items()
    if isinstance(value, type) and issubclass(value, native_element.NativeElement)
}

REFERENCE = re.compile(r"^(?P<path>.+\.py):(?P<screen>\w+)\.(?P<element>\w+)$")


@dataclass(frozen=True)
class Target:
    """An element named on the command line, with the app it belongs to and how it was named."""

    element: Any
    app: Optional[str]
    label: str


def resolve(parts: Sequence[str], window: Optional[AXQuery] = None) -> Target:
    """Return the element `parts` names: `[<module.py>:<Screen>.<element>]` or `[app, locator]`.

    `window` scopes a locator string the way `Screen(window=...)` does.

    Raises:
        ValueError: The locator or the module reference is invalid, or `window` comes with a
            module reference.
    """
    if len(parts) == 1 and (match := REFERENCE.match(parts[0])):
        if window is not None:
            raise ValueError("--window-title and --window-subrole apply to a locator string only")
        return _reference(match, parts[0])
    if len(parts) != 2:
        raise ValueError("Name the element as <app> <locator>, or <module.py>:<Screen>.<element>")
    app, source = parts
    locator = parse_locator(source)
    namespace: dict[str, Any] = {}
    within = getattr(locator, "within", None)
    if within is not None:
        # Declared first, so the element's scope check finds it on the same screen.
        namespace["within"] = within
    namespace["element"] = locator
    screen = type("CommandLine", (Screen,), namespace, app=app, window=window)
    return Target(screen.element, app, source)


def _reference(match: re.Match, label: str) -> Target:
    path = Path(match["path"])
    if not path.is_file():
        raise ValueError(f"No such file: {path}")
    try:
        module = load_module(path)
    # Importing runs the module, which can raise anything.
    except Exception as error:
        raise ValueError(f"Can't load {path}: {error!r}") from error
    screen = getattr(module, match["screen"], None)
    if not (isinstance(screen, type) and issubclass(screen, Screen)):
        raise ValueError(f"{path} has no screen {match['screen']}")
    if not any(isinstance(vars(cls).get(match["element"]), Locator) for cls in screen.__mro__):
        raise ValueError(f"{match['screen']} has no element {match['element']}")
    try:
        element = getattr(screen, match["element"])
    except (TypeError, OSError) as error:
        raise ValueError(f"{path}: {error}") from error
    return Target(element, screen.app, label)


def parse_locator(source: str) -> Locator:
    """Return the locator that `source`, such as `ax(identifier="OK", kind=Button)`, declares.

    Accepts one call to `ax` or `text` with literal arguments, `kind=` naming an
    element class, and `within=` holding a nested `ax()` call. Nothing in `source` is evaluated.

    Raises:
        ValueError: `source` is anything else.
    """
    try:
        node = ast.parse(source, mode="eval").body
    except SyntaxError as error:
        raise ValueError(f"Not a locator: {source!r}") from error
    return _build(node)


def _build(node: ast.expr) -> Locator:
    expected = f"Expected a call to ax() or text(), not {ast.unparse(node)}"
    if not isinstance(node, ast.Call):
        raise ValueError(expected)
    arguments, keywords = _arguments(node)
    function = node.func
    make: Callable[..., Locator]
    if isinstance(function, ast.Attribute) and function.attr == "child":
        parent = _build(function.value)
        if not isinstance(parent, AXLocator):
            raise ValueError(f".child() follows an ax() call, not {ast.unparse(function.value)}")
        make = parent.child
    elif isinstance(function, ast.Name) and function.id in _MODULE_ONLY:
        raise ValueError(f"{_MODULE_ONLY[function.id]}: use <module.py>:<Screen>.<element>")
    elif isinstance(function, ast.Name) and function.id in _FACTORIES:
        make = _FACTORIES[function.id]
    else:
        raise ValueError(expected)
    try:
        return make(*arguments, **keywords)
    except TypeError as error:
        raise ValueError(f"{ast.unparse(node)}: {error}") from error


def _arguments(node: ast.Call) -> tuple[list[Any], dict[str, Any]]:
    arguments = [_literal(argument) for argument in node.args]
    keywords: dict[str, Any] = {}
    for keyword in node.keywords:
        if keyword.arg is None:
            raise ValueError(f"Unpacked arguments aren't allowed: {ast.unparse(node)}")
        if keyword.arg == "kind":
            keywords["kind"] = _kind(keyword.value)
        elif keyword.arg == "within":
            keywords["within"] = _within(keyword.value)
        else:
            keywords[keyword.arg] = _literal(keyword.value)
    return arguments, keywords


def _literal(node: ast.expr) -> Any:
    if isinstance(node, ast.Constant) and isinstance(node.value, (str, int, float, type(None))):
        return node.value
    raise ValueError(f"Only literal strings and numbers are allowed, not {ast.unparse(node)}")


def _kind(node: ast.expr) -> type:
    if isinstance(node, ast.Name) and node.id in _KINDS:
        return _KINDS[node.id]
    raise ValueError(f"kind= takes one of {', '.join(sorted(_KINDS))}, not {ast.unparse(node)}")


def _within(node: ast.expr) -> AXLocator:
    within = _build(node)
    if not isinstance(within, AXLocator):
        raise ValueError(f"within= takes an ax() call, not {ast.unparse(node)}")
    return within
