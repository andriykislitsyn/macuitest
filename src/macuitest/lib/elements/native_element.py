import time
from typing import Any
from typing import Optional

from macuitest.config.constants import Frame
from macuitest.config.constants import Point
from macuitest.config.constants import Region
from macuitest.lib import core
from macuitest.lib.core import wait_condition
from macuitest.lib.elements.controllers.mouse import MouseConfig
from macuitest.lib.elements.controllers.mouse import mouse
from macuitest.lib.elements.native.calls import AXErrorInvalidUIElement


class NativeElement:
    def __init__(self, item):
        self.item = item

    def _select(self):
        self.item.set_ax_attribute("AXSelected", True)

    def _press(self, pause: float = 0.4):
        time.sleep(pause)
        self.item.press()
        time.sleep(0.24)

    def double_click_mouse(
        self, x_off: int = 0, y_off: int = 0, duration: float = MouseConfig.move
    ):
        mouse.double_click(self.frame.center.x + x_off, self.frame.center.y + y_off, duration)

    def click_mouse(
        self,
        x_off: int = 0,
        y_off: int = 0,
        duration: float = MouseConfig.move,
        hold_time: float = MouseConfig.hold,
    ):
        mouse.click(self.frame.center.x + x_off, self.frame.center.y + y_off, hold_time, duration)

    def rightclick_mouse(self, x_off: int = 0, y_off: int = 0, duration=MouseConfig.move):
        mouse.right_click(self.frame.center.x + x_off, self.frame.center.y + y_off, duration)

    def hover_mouse(self, x_off: int = 0, y_off: int = 0, duration: float = MouseConfig.move):
        mouse.hover(self.frame.center.x + x_off, self.frame.center.y + y_off, duration)

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
        self.value = value_

    @property
    def is_visible(self) -> bool:
        return self.exists

    def wait_vanish(self, timeout: [int, float] = 5) -> bool:
        return wait_condition(lambda: self.__get_axrole() is None, timeout=timeout)

    @property
    def did_vanish(self) -> bool:
        return wait_condition(lambda: self.__get_axrole() is None)

    def __get_axrole(self) -> Optional[str]:
        try:
            return self.item.get_ax_attribute("AXRole")
        except (AttributeError, IndexError):
            pass

    @property
    def exists(self) -> bool:
        return self.item is not None


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
