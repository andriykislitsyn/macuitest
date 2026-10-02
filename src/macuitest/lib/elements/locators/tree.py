"""Print an app's accessibility tree with the `ax()` locator of each element."""

from typing import Any
from typing import Optional
from typing import Sequence

from macuitest.lib.core import wait_condition
from macuitest.lib.elements.locators.accessibility import GONE
from macuitest.lib.elements.locators.accessibility import AXQuery
from macuitest.lib.elements.locators.accessibility import app_root
from macuitest.lib.elements.locators.accessibility import standard_window
from macuitest.lib.elements.locators.accessibility import windows
from macuitest.lib.elements.locators.capture import WINDOW_TIMEOUT
from macuitest.lib.elements.locators.capture import Found
from macuitest.lib.elements.locators.capture import _label
from macuitest.lib.elements.locators.capture import _literal
from macuitest.lib.elements.locators.capture import locator_for
from macuitest.lib.elements.locators.capture import walk

VALUE_LENGTH = 40


def tree(
    app: str,
    window: Optional[AXQuery] = None,
    roles: Sequence[str] = (),
    activate: bool = False,
) -> str:
    """Return `app`'s windows and their elements, one indented line each.

    Each element line shows its role, identifier, description, title, and value, then the `ax()`
    locator that finds it, when one does. `window` keeps only the first matching window, and
    `roles` keeps only elements with those AX roles. Leaves the app in the background unless
    `activate` is set.

    Raises:
        LookupError: The app isn't running, or has no matching window.
        PermissionError: Accessibility isn't granted.
    """
    if activate:
        root = app_root(app)
        try:
            if root is not None:
                root.activate()
        except GONE:
            pass
    roots = wait_condition(lambda: _roots(app, window), timeout=WINDOW_TIMEOUT if activate else 0)
    if not roots:
        if window is not None:
            raise LookupError(f"{app} has no window with {window}")
        hint = "" if activate else ". Some apps show windows only while active: pass --activate"
        raise LookupError(f"{app} isn't running, or has no windows in the accessibility tree{hint}")
    walked = [walk(root) for root in roots]
    # An ax() lookup searches every window front to back, so locators count all of them.
    everything = [found for elements in walked for found in elements]
    lines = []
    for root, elements in zip(roots, walked, strict=True):
        lines.append(
            _line("AXWindow", title=_label(root, "AXTitle"), subrole=_label(root, "AXSubrole"))
        )
        for found in elements:
            if not roles or found.role in roles:
                lines.append("  " * found.depth + _element(found, everything))
    return "\n".join(lines) + "\n"


def _roots(app: str, window: Optional[AXQuery]) -> list[Any]:
    if window is None:
        return windows(app)
    match = standard_window(app, window)
    return [] if match is None else [match]


def _element(found: Found, walked: list[Found]) -> str:
    role = f"{found.role} [chrome]" if found.chrome else found.role
    line = _line(
        role,
        identifier=found.identifier,
        description=found.description,
        title=found.title,
        value=_value(found.value),
    )
    locator, _ = locator_for(found, walked)
    return line if locator == "image()" else f"{line}  {locator}"


def _line(role: str, **attributes: Optional[str]) -> str:
    shown = [f"{name}={_literal(value)}" for name, value in attributes.items() if value is not None]
    return " ".join([role, *shown])


def _value(value: Any) -> Optional[str]:
    if not isinstance(value, (str, int, float)):
        return None
    text = str(value)
    return text if len(text) <= VALUE_LENGTH else text[:VALUE_LENGTH] + "…"
