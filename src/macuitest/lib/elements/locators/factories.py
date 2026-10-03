"""Element factories for `Screen` attributes."""

from pathlib import Path
from typing import Any
from typing import Optional
from typing import TypeVar
from typing import overload

from macuitest.config.constants import Region
from macuitest.lib.elements.applescript_element import BaseUIElement
from macuitest.lib.elements.locators.accessibility import GONE
from macuitest.lib.elements.locators.accessibility import AXQuery
from macuitest.lib.elements.locators.accessibility import find_first
from macuitest.lib.elements.locators.accessibility import frame_of
from macuitest.lib.elements.locators.accessibility import standard_window
from macuitest.lib.elements.locators.accessibility import standard_window_frame
from macuitest.lib.elements.locators.accessibility import windows
from macuitest.lib.elements.locators.screen import CachedLocator
from macuitest.lib.elements.locators.screen import Locator
from macuitest.lib.elements.locators.screen import image_folder
from macuitest.lib.elements.native_element import NativeElement
from macuitest.lib.elements.screen_element import Scope
from macuitest.lib.elements.ui_element import UIElement
from macuitest.lib.elements.visible_text import VisibleText

A = TypeVar("A", bound=BaseUIElement)
E = TypeVar("E", bound=NativeElement)


class AXLocator(Locator[E]):
    def __init__(self, queries: tuple[AXQuery, ...], kind: type[E]):
        self.queries, self.kind = queries, kind

    def child(
        self,
        identifier: Optional[str] = None,
        description: Optional[str] = None,
        title: Optional[str] = None,
        role: Optional[str] = None,
        kind: Optional[type[NativeElement]] = None,
    ) -> "AXLocator[Any]":
        """Return a locator for this element's first descendant matching the given attributes.

        The descendant reads as a `kind` instance, by default this element's kind.
        """
        query = AXQuery.of(identifier=identifier, description=description, title=title, role=role)
        return AXLocator((*self.queries, query), kind or self.kind)

    def find(self) -> Optional[Any]:
        """Return the accessibility element, or None when the app or element isn't there.

        Raises:
            TypeError: The screen has no app.
        """
        app = self._app()
        match = None
        if self.screen.window is None:
            roots = windows(app)
        else:
            screen_window = standard_window(app, self.screen.window)
            roots = [] if screen_window is None else [screen_window]
        for query in self.queries:
            match = find_first(roots, query)
            if match is None:
                return None
            roots = [match]
        return match

    def region(self) -> Optional[Region]:
        """Return the element's frame, or None when it isn't there."""
        element = self.find()
        try:
            return None if element is None else frame_of(element)
        except GONE:
            return None

    def resolve(self) -> E:
        self._app()
        return self.kind(find=self._require)

    def _app(self) -> str:
        if self.screen.app is None:
            raise TypeError(f"{self.qualified_name}: ax() needs a Screen declared with app=")
        return self.screen.app

    def _require(self) -> Any:
        element = self.find()
        if element is None:
            path = " > ".join(map(str, self.queries))
            window = "windows" if self.screen.window is None else f"{self.screen.window} window"
            raise LookupError(
                f"{self.qualified_name}: no element with {path} in {self.screen.app}'s {window}"
            )
        return element


def check_within(locator: Locator, within: Optional[AXLocator]) -> None:
    """Raise unless `within` is None or an `ax()` element of `locator`'s screen.

    Raises:
        TypeError: `within` belongs to another screen or isn't an `ax()` element.
    """
    if within is None:
        return
    if not isinstance(within, AXLocator) or getattr(within, "screen", None) is not locator.screen:
        raise TypeError(
            f"{locator.qualified_name}: within= takes an ax() element of {locator.screen.__name__}"
        )


def scope_for(locator: Locator, within: Optional[AXLocator]) -> Optional[Scope]:
    """Return the search area of a text or image element.

    That is `within`'s frame when given, else the screen's window, else None for the default.
    """
    if within is not None:
        return within.region
    app, query = locator.screen.app, locator.screen.window
    if app is None:
        return None
    return lambda: standard_window_frame(app, query)


class TextLocator(Locator[VisibleText]):
    def __init__(self, label: str, within: Optional[AXLocator]):
        # Built now, so a label Vision can't read fails when the module is imported.
        self.element = VisibleText(label)
        self.within = within
        self.scoped = False

    def __set_name__(self, owner: type, name: str) -> None:
        super().__set_name__(owner, name)
        check_within(self, self.within)

    def resolve(self) -> VisibleText:
        # Python sets descriptor names before `Screen.__init_subclass__` records `app`.
        if not self.scoped:
            self.element.scope = scope_for(self, self.within)
            self.scoped = True
        return self.element


class ImageLocator(CachedLocator[UIElement]):
    def __init__(
        self, file_name: Optional[str], similarity: Optional[float], within: Optional[AXLocator]
    ):
        self.file_name = file_name or ""
        self.similarity = similarity
        self.within = within

    def __set_name__(self, owner: type, name: str) -> None:
        super().__set_name__(owner, name)
        check_within(self, self.within)
        self.file_name = self.file_name or name

    @property
    def path(self) -> Path:
        """Where this element's PNG lives."""
        folder = image_folder(self.module_file(), self.screen.__name__)
        return folder / f"{self.file_name}.png"

    def build(self) -> UIElement:
        element = UIElement(self.path, similarity=self.similarity)
        element.scope = scope_for(self, self.within)
        return element


class AppleScriptLocator(CachedLocator[A]):
    def __init__(self, locator: str, kind: type[A], process: Optional[str]):
        self.locator, self.kind, self.process = locator, kind, process

    def build(self) -> A:
        process = self.process or self.screen.app
        if process is None:
            raise TypeError(
                f"{self.qualified_name}: pass process=, or declare {self.screen.__name__} with app="
            )
        return self.kind(self.locator, process=process)


def window(title: Optional[str] = None, subrole: Optional[str] = None) -> AXQuery:
    """Return the window a `Screen` covers, by its `AXTitle` and `AXSubrole`, such as "AXDialog".

    Raises:
        TypeError: Neither is given.
    """
    return AXQuery.of(title=title, subrole=subrole)


def text(label: str, within: Optional[AXLocator] = None) -> TextLocator:
    """Declare visible text, found with Apple Vision in `within`, else in the screen app's window.

    Raises:
        ValueError: `label` is a single character.
        TypeError: `within` isn't an `ax()` element of the same screen.
    """
    return TextLocator(label, within)


def image(
    name: Optional[str] = None,
    similarity: Optional[float] = None,
    within: Optional[AXLocator] = None,
) -> ImageLocator:
    """Declare an element found by its screenshot, `<name>.png` in the screen's image folder.

    `name` defaults to the attribute name. A missing PNG raises `FileNotFoundError` on first read.
    The lookup searches `within`, else the screen app's window.

    Raises:
        TypeError: `within` isn't an `ax()` element of the same screen.
    """
    return ImageLocator(name, similarity, within)


@overload
def applescript(
    locator: str, *, process: Optional[str] = None
) -> AppleScriptLocator[BaseUIElement]: ...
@overload
def applescript(
    locator: str, kind: type[A], process: Optional[str] = None
) -> AppleScriptLocator[A]: ...
def applescript(locator, kind=BaseUIElement, process=None):
    """Declare an element found with an AppleScript locator, as a `kind` instance.

    `process` defaults to the screen's app. Reading the element without either raises `TypeError`.
    """
    return AppleScriptLocator(locator, kind, process)


@overload
def ax(
    *,
    identifier: Optional[str] = None,
    description: Optional[str] = None,
    title: Optional[str] = None,
    role: Optional[str] = None,
) -> AXLocator[NativeElement]: ...
@overload
def ax(
    *,
    identifier: Optional[str] = None,
    description: Optional[str] = None,
    title: Optional[str] = None,
    role: Optional[str] = None,
    kind: type[E],
) -> AXLocator[E]: ...
def ax(*, identifier=None, description=None, title=None, role=None, kind=NativeElement):
    """Declare an element found by accessibility attributes in the screen app's windows.

    Matches `AXIdentifier`, `AXDescription`, `AXTitle`, and `AXRole`, and reads as a `kind`
    instance that finds the element again on every use. A missing element reads as not visible,
    and any other use of it raises `LookupError`.

    Raises:
        TypeError: No attribute is given.
    """
    query = AXQuery.of(identifier=identifier, description=description, title=title, role=role)
    return AXLocator((query,), kind)
