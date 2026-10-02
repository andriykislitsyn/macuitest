"""Element factories for `Screen` attributes."""

from pathlib import Path
from typing import Optional
from typing import TypeVar
from typing import overload

from macuitest.lib.elements.applescript_element import BaseUIElement
from macuitest.lib.elements.locators.ax import standard_window_frame
from macuitest.lib.elements.locators.screen import CachedLocator
from macuitest.lib.elements.locators.screen import Locator
from macuitest.lib.elements.locators.screen import image_folder
from macuitest.lib.elements.screen_element import Scope
from macuitest.lib.elements.ui_element import UIElement
from macuitest.lib.elements.visible_text import VisibleText

A = TypeVar("A", bound=BaseUIElement)


def scope_for(locator: Locator) -> Optional[Scope]:
    """Return the search area of a text or image element: its app's window, if it has an app."""
    app = locator.screen.app
    if app is None:
        return None
    return lambda: standard_window_frame(app)


class TextLocator(Locator[VisibleText]):
    def __init__(self, label: str):
        # Built now, so a label Vision can't read fails when the module is imported.
        self.element = VisibleText(label)
        self.scoped = False

    def resolve(self) -> VisibleText:
        # Python sets descriptor names before `Screen.__init_subclass__` records `app`.
        if not self.scoped:
            self.element.scope = scope_for(self)
            self.scoped = True
        return self.element


class ImageLocator(CachedLocator[UIElement]):
    def __init__(self, file_name: Optional[str], similarity: Optional[float]):
        self.file_name = file_name or ""
        self.similarity = similarity

    def __set_name__(self, owner: type, name: str) -> None:
        super().__set_name__(owner, name)
        self.file_name = self.file_name or name

    @property
    def path(self) -> Path:
        """Where this element's PNG lives."""
        folder = image_folder(self.module_file(), self.screen.__name__)
        return folder / f"{self.file_name}.png"

    def build(self) -> UIElement:
        element = UIElement(self.path, similarity=self.similarity)
        element.scope = scope_for(self)
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


def text(label: str) -> TextLocator:
    """Declare visible text, found with Apple Vision in the screen app's window.

    Raises:
        ValueError: `label` is a single character.
    """
    return TextLocator(label)


def image(name: Optional[str] = None, similarity: Optional[float] = None) -> ImageLocator:
    """Declare an element found by its screenshot, `<name>.png` in the screen's image folder.

    `name` defaults to the attribute name. A missing PNG raises `FileNotFoundError` on first read.
    """
    return ImageLocator(name, similarity)


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
