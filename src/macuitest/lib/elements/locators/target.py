"""Turn a command line target, a locator string or a `Screen` attribute, into an element."""

import ast
from typing import Any
from typing import Callable

from macuitest.lib.elements import applescript_element
from macuitest.lib.elements import native_element
from macuitest.lib.elements.locators.factories import AXLocator
from macuitest.lib.elements.locators.factories import applescript
from macuitest.lib.elements.locators.factories import ax
from macuitest.lib.elements.locators.factories import text
from macuitest.lib.elements.locators.screen import Locator

_FACTORIES: dict[str, Callable[..., Locator]] = {"applescript": applescript, "ax": ax, "text": text}
# `kind=` names by factory, since both element modules define a Button.
_KINDS = {
    "ax": {
        name: value
        for name, value in vars(native_element).items()
        if isinstance(value, type) and issubclass(value, native_element.NativeElement)
    },
    "applescript": {
        name: value
        for name, value in vars(applescript_element).items()
        if isinstance(value, type) and issubclass(value, applescript_element.BaseUIElement)
    },
}


def parse_locator(source: str) -> Locator:
    """Return the locator that `source`, such as `ax(identifier="OK", kind=Button)`, declares.

    Accepts one call to `ax`, `text`, or `applescript` with literal arguments, `kind=` naming an
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
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "image":
        raise ValueError("image() needs a Screen module: use <module.py>:<Screen>.<element>")
    if not (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id in _FACTORIES
    ):
        raise ValueError(
            f"Expected a call to ax(), text(), or applescript(), not {ast.unparse(node)}"
        )
    factory = node.func.id
    arguments = [_literal(argument) for argument in node.args]
    keywords: dict[str, Any] = {}
    for keyword in node.keywords:
        if keyword.arg is None:
            raise ValueError(f"Unpacked arguments aren't allowed: {ast.unparse(node)}")
        if keyword.arg == "kind":
            keywords["kind"] = _kind(factory, keyword.value)
        elif keyword.arg == "within":
            keywords["within"] = _within(keyword.value)
        else:
            keywords[keyword.arg] = _literal(keyword.value)
    try:
        return _FACTORIES[factory](*arguments, **keywords)
    except TypeError as error:
        raise ValueError(f"{ast.unparse(node)}: {error}") from error


def _literal(node: ast.expr) -> Any:
    if isinstance(node, ast.Constant) and isinstance(node.value, (str, int, float, type(None))):
        return node.value
    raise ValueError(f"Only literal strings and numbers are allowed, not {ast.unparse(node)}")


def _kind(factory: str, node: ast.expr) -> type:
    kinds = _KINDS.get(factory, {})
    if isinstance(node, ast.Name) and node.id in kinds:
        return kinds[node.id]
    raise ValueError(f"kind= takes one of {', '.join(sorted(kinds))}, not {ast.unparse(node)}")


def _within(node: ast.expr) -> AXLocator:
    within = _build(node)
    if not isinstance(within, AXLocator):
        raise ValueError(f"within= takes an ax() call, not {ast.unparse(node)}")
    return within
