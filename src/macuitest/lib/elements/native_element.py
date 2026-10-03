import time
from typing import Any
from typing import Callable
from typing import Optional

from macuitest.config.constants import Frame
from macuitest.config.constants import Point
from macuitest.config.constants import Region
from macuitest.config.settings import settings
from macuitest.lib import core
from macuitest.lib.core import wait_condition
from macuitest.lib.elements.controllers.mouse import mouse
from macuitest.lib.elements.native.calls import AXErrorInvalidUIElement


class NativeElement:
    def __init__(self, item: Any = None, find: Optional[Callable[[], Any]] = None):
        """Wrap a fixed accessibility element, or a `find` callable that searches on every read.

        Args:
            item: The accessibility element.
            find: Returns the element, or raises `LookupError` when it isn't there. Wins over
                `item`.
        """
        self._item, self._find = item, find

    @property
    def item(self) -> Any:
        return self._item if self._find is None else self._find()

    def _select(self):
        self.item.set_ax_attribute("AXSelected", True)

    def _press(self, pause: float = 0.4):
        time.sleep(pause)
        self.item.press()
        time.sleep(0.24)

    def click_mouse(
        self,
        x_off: int = 0,
        y_off: int = 0,
        *,
        hold: Optional[float] = None,
        duration: Optional[float] = None,
        pause: Optional[float] = None,
    ):
        center = self.frame.center
        mouse.click(center.x + x_off, center.y + y_off, hold=hold, duration=duration, pause=pause)

    def double_click_mouse(
        self, x_off: int = 0, y_off: int = 0, *, duration: Optional[float] = None
    ):
        center = self.frame.center
        mouse.double_click(center.x + x_off, center.y + y_off, duration=duration)

    def right_click_mouse(
        self,
        x_off: int = 0,
        y_off: int = 0,
        *,
        hold: Optional[float] = None,
        duration: Optional[float] = None,
        pause: Optional[float] = None,
    ):
        center = self.frame.center
        mouse.right_click(
            center.x + x_off, center.y + y_off, hold=hold, duration=duration, pause=pause
        )

    def hover_mouse(self, x_off: int = 0, y_off: int = 0, *, duration: Optional[float] = None):
        center = self.frame.center
        mouse.hover(center.x + x_off, center.y + y_off, duration=duration)

    def region(self, margin: int = 0):
        return Region(
            self.frame.x1 - margin,
            self.frame.y1 - margin,
            self.frame.x2 + margin,
            self.frame.y2 + margin,
        )

    @property
    def frame(self) -> Frame:
        _frame = [*self.item.get_ax_attribute("AXPosition"), *self.item.get_ax_attribute("AXSize")]
        x1, y1, width, height = _frame
        x2, y2 = x1 + width, y1 + height
        center = Point(int((x1 + width / 2)), int((y1 + height / 2)))
        return Frame(x1, y1, x2, y2, center, width, height)

    @property
    def characters_number(self) -> int:
        return self.item.get_ax_attribute("AXNumberOfCharacters")

    @property
    def title(self) -> str:
        return self.item.get_ax_attribute("AXTitle")

    @property
    def help(self) -> str:
        return self.item.get_ax_attribute("AXHelp")

    @property
    def parent(self):
        return NativeElement(self.item.get_ax_attribute("AXParent"))

    @property
    def children(self):
        try:
            return self.item.get_ax_attribute("AXChildren")
        except AttributeError:
            return []

    @property
    def value(self) -> Any:
        return self.item.get_ax_attribute("AXValue")

    @value.setter
    def value(self, value_) -> None:
        self.item.set_ax_attribute("AXValue", value_)

    @property
    def is_visible(self) -> bool:
        """Whether the element is in the accessibility tree now. Doesn't wait."""
        return self.exists

    def wait_displayed(self, timeout: Optional[float] = None) -> bool:
        """Return whether the element appears within `timeout` seconds.

        `timeout` defaults to `settings.elements.timeout`.
        """
        timeout = settings.elements.timeout if timeout is None else timeout
        return bool(wait_condition(lambda: self.exists, timeout=timeout))

    def wait_vanish(self, timeout: Optional[float] = None) -> bool:
        """Return whether the element disappears within `timeout` seconds.

        `timeout` defaults to `settings.elements.vanish_timeout`.
        """
        timeout = settings.elements.vanish_timeout if timeout is None else timeout
        return wait_condition(lambda: self.__get_axrole() is None, timeout=timeout)

    def __get_axrole(self) -> Optional[str]:
        try:
            return self.item.get_ax_attribute("AXRole")
        except (AttributeError, LookupError):
            pass

    @property
    def exists(self) -> bool:
        try:
            return self.item is not None
        except LookupError:
            return False


class Clickable(NativeElement):
    @property
    def is_enabled(self) -> bool:
        return self.item.get_ax_attribute("AXEnabled")

    def press(self, pause: float = 0.375):
        self._press(pause=pause)

    def click(self, pause: float = 0.375):
        self._press(pause=pause)


class Cell(NativeElement):
    def select(self):
        self._select()


class Row(NativeElement):
    def select(self):
        self._select()

    @property
    def is_selected(self) -> bool:
        return self.item.get_ax_attribute("AXSelected")

    @is_selected.setter
    def is_selected(self, value):
        self.item.set_ax_attribute("AXSelected", value)


class Button(Clickable):
    pass


class Image(NativeElement):
    @property
    def label(self) -> str:
        return self.item.get_ax_attribute("AXLabel")


class StaticText(NativeElement):
    @property
    def to_bytes(self) -> int:
        return core.convert_file_size_to_bytes(self.text)

    @property
    def text(self) -> str:
        return str(self.value)

    def __eq__(self, other):
        return wait_condition(lambda: self.text == other, timeout=2)


class TextField(StaticText):
    @property
    def text(self) -> str:
        return str(self.item.get_ax_attribute("AXValue"))

    @text.setter
    def text(self, value):
        self.item.set_ax_attribute("AXValue", value)

    @property
    def placeholder(self) -> str:
        return str(self.item.get_ax_attribute("AXPlaceholderValue"))

    @property
    def keyboard_focused(self) -> bool:
        return self.item.get_ax_attribute("AXFocused")

    @keyboard_focused.setter
    def keyboard_focused(self, value):
        self.item.set_ax_attribute("AXFocused", bool(value))

    def __eq__(self, other):
        return wait_condition(lambda: self.text == other, timeout=2)


class CheckBox(Clickable):
    @property
    def state(self) -> int:
        return self.value

    @state.setter
    def state(self, value: bool) -> None:
        for _ in range(3):
            if self.state != value:
                self._press()


class DisclosureTriangle(CheckBox):
    pass


class MenuItem(Clickable):
    pass


class Link(NativeElement):
    @property
    def url(self) -> str:
        return str(self.item.get_ax_attribute("AXURL"))


class WebView(NativeElement):
    @property
    def url(self) -> str:
        webview = self.__perform_lookup()
        wait_condition(lambda: webview.get_ax_attribute("AXURL"), timeout=30)
        wait_condition(lambda: webview.get_ax_attribute("AXURL").startswith("https://"), timeout=30)
        return str(webview.get_ax_attribute("AXURL"))

    def __perform_lookup(self):
        self.__wait_children()
        return self.item.find_element(AXRole="AXUnknown", recursive=True)

    def __wait_children(self):
        wait_condition(
            lambda: self.item.get_ax_attribute("AXChildren"),
            exceptions=(AttributeError, AXErrorInvalidUIElement),
        )
