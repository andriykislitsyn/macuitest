import time
from typing import Any, Optional

from macuitest.config.constants import Frame, Point, Region
from macuitest.lib import core
from macuitest.lib.core import wait_condition
from macuitest.lib.elements.native.errors import AXErrorFactory, AXErrorInvalidUIElement
from macuitest.lib.elements.controllers.mouse import mouse


class NativeElement:
    def __init__(self, item):
        self.item = item

    def _select(self):
        self.item.AXSelected = True

    def _press(self, pause: float = 0.375):
        time.sleep(pause)
        self.item.AXPress()
        time.sleep(.2)

    def double_click_mouse(self, x_off=0, y_off=0, duration=.2):
        mouse.double_click(self.frame.center.x + x_off, self.frame.center.y + y_off, duration)

    def click_mouse(self, x_off=0, y_off=0, duration=.2, hold_time=.3):
        mouse.click(self.frame.center.x + x_off, self.frame.center.y + y_off, hold_time, duration)

    def rightclick_mouse(self, x_off=0, y_off=0, duration=.2):
        mouse.right_click(self.frame.center.x + x_off, self.frame.center.y + y_off, duration)

    def hover_mouse(self, x_off=0, y_off=0, duration=.2):
        mouse.hover(self.frame.center.x + x_off, self.frame.center.y + y_off, duration)

    def region(self, margin: int = 4):
        return Region(self.frame.x1 - margin, self.frame.y1 - margin, self.frame.x2 + margin, self.frame.y2 + margin)

    @property
    def frame(self) -> Frame:
        _frame = [*self.item.AXPosition, *self.item.AXSize]
        x1, y1, width, height = _frame
        x2, y2 = x1 + width, y1 + height
        center = Point(int((x1 + width / 2)), int((y1 + height / 2)))
        return Frame(x1, y1, x2, y2, center, width, height)

    @property
    def characters_number(self) -> int:
        return self.item.AXNumberOfCharacters

    @property
    def title(self) -> str:
        return self.item.AXTitle

    @property
    def help(self) -> str:
        return self.item.AXHelp

    @property
    def parent(self):
        return NativeElement(self.item.AXParent)

    @property
    def children(self):
        try:
            return self.item.AXChildren
        except AttributeError:
            return []

    @property
    def value(self) -> Any:
        return self.item.AXValue

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
            return self.item.AXRole
        except (AttributeError, IndexError):
            pass

    @property
    def exists(self) -> bool:
        return self.item is not None


class Clickable(NativeElement):
    @property
    def is_enabled(self) -> bool:
        return self.item.AXEnabled

    def press(self, pause: float = .375):
        self._press(pause=pause)

    def click(self, pause: float = .375):
        self._press(pause=pause)


class Cell(NativeElement):
    def select(self):
        self._select()


class Row(NativeElement):
    def select(self):
        self._select()

    @property
    def is_selected(self) -> bool:
        return self.item.AXSelected

    @is_selected.setter
    def is_selected(self, value):
        self.item.AXSelected = value


class Button(Clickable):
    pass


class Image(NativeElement):
    @property
    def label(self) -> str:
        return self.item.AXLabel


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
        return str(self.item.AXValue)

    @text.setter
    def text(self, value):
        self.item.AXValue = value

    @property
    def keyboard_focused(self) -> bool:
        return self.item.AXFocused

    @keyboard_focused.setter
    def keyboard_focused(self, value):
        self.item.AXFocused = bool(value)

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
        return str(self.item.AXURL)


class WebView(NativeElement):

    @property
    def url(self) -> str:
        webview = self.__perform_lookup()
        wait_condition(lambda: webview.AXURL, timeout=30)
        wait_condition(lambda: webview.AXURL.startswith('https://'), timeout=30)
        return str(webview.AXURL)

    def __perform_lookup(self):
        self.__wait_children()
        return self.item.find_element(AXRole='AXUnknown', recursive=True)

    def __wait_children(self):
        for _ in range(20):
            try:
                time.sleep(0.3)
                return self.item.AXChildren
            except (AttributeError, AXErrorInvalidUIElement, AXErrorFactory):
                continue
