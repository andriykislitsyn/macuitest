import os
import time
from dataclasses import dataclass
from datetime import datetime
from types import MappingProxyType
from typing import Any, Union, Optional, Tuple

from macuitest.config.constants import CheckboxState, Frame, Point, DisclosureTriangleState, Region
from macuitest.lib import core
from macuitest.lib.applescript_lib.applescript_wrapper import as_wrapper, AppleScriptError
from macuitest.lib.core import wait_condition
from macuitest.lib.elements.controllers.mouse import mouse
from macuitest.lib.operating_system.color_meter import ColorMeter
from macuitest.lib.operating_system.env import env


class BaseUIElement:
    """Default AppleScript UI element."""
    __slots__ = ('locator', 'process', '_frame')

    def __init__(self, locator, process):
        self.locator = locator
        self.process = process
        self._frame = None

    def __repr__(self):
        return f"<{self.__class__.__name__}|locator='{self.locator}', process='{self.process}'>"

    def wait_on_position(self, position: Point) -> bool:
        self.reset_frame()
        return self.frame.center == position

    def snapshot(self, margin: int = 4) -> str:
        self.reset_frame()
        _region = f'{self.frame.x1 - margin},{self.frame.y1 - margin},' \
                  f'{self.frame.width + margin * 2},{self.frame.height + margin * 2}'
        _where = f'{env.desktop}/scr_{datetime.now().strftime("%Y%m%d%H%M%S%f")}.png'
        os.system(f'screencapture -x -R"{_region}" "{_where}"')
        return _where

    def region(self, margin: int = 4):
        self.reset_frame()
        return Region(self.frame.x1 - margin, self.frame.y1 - margin, self.frame.x2 + margin, self.frame.y2 + margin)

    def most_common_color(self, ignore_colors: Optional[Tuple[str, ...]] = None):
        self.reset_frame()
        f = self.frame
        return ColorMeter().get_most_common_color(f.x1, f.x2, f.y1, f.y2, ignore_colors)

    def color(self, x_off: int = 0, y_off: int = 0) -> str:
        self.reset_frame()
        pixel_color = ColorMeter().get_color(Point(self.frame.center.x + x_off, self.frame.center.y + y_off))
        return pixel_color.replace('gray', 'grey')

    def scroll(self, clicks, x_off=0, y_off=0):
        self.__assert_visible()
        mouse.scroll(self.frame.center.x + x_off, self.frame.center.y + y_off, clicks, x_off, y_off)

    def doubleclick_mouse(self, x_off: int = 0, y_off: int = 0, duration: Union[int, float] = 0.15):
        self.__assert_visible()
        mouse.double_click(self.frame.center.x + x_off, self.frame.center.y + y_off, duration=duration)
        self.reset_frame()

    def rightclick_mouse(self, x_off=0, y_off=0, duration=.2) -> None:
        self.__assert_visible()
        mouse.right_click(self.frame.center.x + x_off, self.frame.center.y + y_off, duration)
        self.reset_frame()

    def click_mouse(self, x_off=0, y_off=0, hold_time=.3, duration=.2, pause=.3) -> None:
        if not self.wait_displayed(timeout=7):
            raise LookupError(self)
        mouse.click(self.frame.center.x + x_off, self.frame.center.y + y_off, hold_time, duration, pause)
        self.reset_frame()

    def hover_mouse(self, x_off: int = 0, y_off: int = 0, duration: float = .2) -> None:
        mouse.hover(self.frame.center.x + x_off, self.frame.center.y + y_off, duration=duration)

    def click(self, pause: float = 0.375) -> bool:
        """Perform click action the element."""
        self.__assert_visible()
        time.sleep(pause)
        self.__execute('click')
        time.sleep(0.2)
        return True

    def _select(self):
        """Click an element."""
        self.__assert_visible()
        return self.__execute('select')

    def _set_focus(self, value):
        """Make element focused."""
        self.__assert_visible()
        return self.__execute('set focused of', params=f'to "{value}"')

    def _show_context_menu(self):
        self.__assert_visible()
        return self.__execute('perform action "AXShowMenu" of')

    def _set_value(self, value):
        """Set element value."""
        self.__assert_visible()
        return self.__execute('set value of', params=f'to "{value}"')

    def _get_value(self):
        """Get element value."""
        self.__assert_visible()
        return self.__execute('get value of')

    def _count_elements(self) -> int:
        """Count UI elements """
        self.__assert_visible()
        return self.__execute('count UI elements of')

    @property
    def _children(self):
        self.__assert_visible()
        return self._read_attribute('AXChildren')

    @property
    def _rows(self) -> int:
        self.__assert_visible()
        return self.__execute('count rows of')

    @property
    def frame(self) -> Frame:
        if self._frame is not None:
            return self._frame
        self.__assert_visible()
        _frame = [*self._read_attribute('AXPosition'), *self._read_attribute('AXSize')]
        x1, y1, width, height = _frame
        x2, y2 = x1 + width, y1 + height
        center = Point(int((x1 + width / 2)), int((y1 + height / 2)))
        self._frame = Frame(x1, y1, x2, y2, center, width, height)
        return self._frame

    def reset_frame(self):
        self._frame = None

    @property
    def title(self) -> str:
        self.__assert_visible()
        return self._read_attribute('AXTitle').strip()

    @property
    def description(self) -> str:
        self.__assert_visible()
        return self._read_attribute('AXDescription').strip()

    @property
    def value(self) -> str:
        self.__assert_visible()
        return self._read_attribute('AXValue')

    @property
    def help(self) -> str:
        self.__assert_visible()
        return self._read_attribute('AXHelp')

    @property
    def _placeholder(self) -> str:
        self.__assert_visible()
        return self._read_attribute('AXPlaceholderValue')

    def _is_enabled(self) -> bool:
        """Check whether element enabled"""
        self.__assert_visible()
        return self._read_attribute('AXEnabled')

    @property
    def did_vanish(self) -> bool:
        return self.wait_vanish()

    def wait_vanish(self, timeout: [int, float] = 5) -> bool:
        self.wait_displayed(timeout=0.3)
        return wait_condition(lambda: self.is_exists() is False, timeout=timeout)

    @property
    def is_visible(self) -> bool:
        return self.wait_displayed()

    def wait_displayed(self, timeout: Union[int, float] = 5):
        return wait_condition(self.is_exists, timeout=timeout)

    def _set_attribute(self, attribute, value) -> Any:
        return self.__execute(f'set value of attribute "{attribute}" of', params=f'to {value}')

    def _read_attribute(self, attribute) -> Any:
        try:
            return self.__execute(f'get value of attribute "{attribute}" of')
        except AppleScriptError:
            return None

    def is_exists(self) -> bool:
        try:
            return self.__execute(f'return exists')
        except AppleScriptError as e:
            if e.number == -10000:
                pass
            else:
                raise

    def __assert_visible(self):
        if not self.is_visible:
            raise LookupError(self)

    def __execute(self, command, params=''):
        """Execute a command.
               :param str command: The name of the command to _execute as a string.
               :param str params: Command parameters.
               :return str: Execution output."""
        _command = f'{command} {self.locator} {params}' if params else f'{command} {self.locator}'
        return as_wrapper.tell_app_process(command=_command, app_process=self.process)


class Button(BaseUIElement):
    @property
    def is_enabled(self):
        return wait_condition(self._is_enabled)

    def wait_enabled(self, timeout: int) -> bool:
        return wait_condition(self._is_enabled, timeout=timeout)

    @property
    def is_disabled(self):
        return wait_condition(lambda: self._is_enabled() is False)

    @property
    def value(self):
        return self._get_value()


class BusyIndicator(BaseUIElement):
    pass


class TextElement(BaseUIElement):
    def __repr__(self):
        try:
            return f"'{self.text}'"
        except (AppleScriptError, LookupError):
            return f"{self.__class__.__name__}(locator='{self.locator}', process='{self.process}')"

    @property
    def to_bytes(self) -> int:
        return core.convert_file_size_to_bytes(self.text)

    @property
    def characters_number(self):
        return self._read_attribute('AXNumberOfCharacters')

    @property
    def visible_characters_number(self):
        return list(self._read_attribute('AXVisibleCharacterRange'))[1]

    def set_text(self, value: str):
        self.wait_displayed()
        self._set_focus(True)
        self._set_value(value)

    def get_text(self) -> str:
        self.wait_displayed(timeout=1)
        return str(self._get_value())

    @property
    def is_fully_visible(self):
        self.wait_displayed(timeout=1)
        return self.characters_number == self.visible_characters_number

    def __eq__(self, other):
        return wait_condition(lambda: self.text == other, timeout=1)

    text = property(get_text, set_text)


class StaticText(TextElement):
    pass


class TextArea(TextElement):
    pass


class TextField(TextElement):
    @property
    def placeholder(self):
        return self._placeholder

    def value(self) -> str:
        return self._get_value()

    def set(self, value):
        self._set_value(value)

    def focus(self, value='true'):
        self._set_focus(value)

    @property
    def is_focused(self):
        return self._read_attribute('AXFocused')

    @is_focused.setter
    def is_focused(self, value: bool):
        self._set_focus(value)

    text = property(value, set)


class ComboBox(BaseUIElement):
    def value(self) -> str:
        return self._get_value()

    def set_value(self, value):
        self.wait_displayed()
        time.sleep(0.5)
        self._set_value(value)

    text = property(value, set_value)


class Checkbox(BaseUIElement):
    @property
    def is_enabled(self):
        return wait_condition(self._is_enabled, timeout=3)

    @property
    def is_disabled(self):
        return wait_condition(lambda: self._is_enabled() is False)

    def wait_state(self, state):
        return wait_condition(lambda: self.get_state() == state)

    def set_state(self, state):
        target_state = CheckboxState.states.get(state)
        for _ in range(2):
            if self.get_state() != target_state:
                self.click()
        assert self.state == target_state, f'Cannot set checkbox to state: "{state}"'

    def get_state(self):
        return self._get_value()

    state = property(get_state, set_state)


class DisclosureTriangle(BaseUIElement):
    def get_state(self):
        return self._get_value()

    def set_state(self, state: DisclosureTriangleState):
        attempts_left = 2
        while self.state != state and attempts_left:
            self.click()
            attempts_left -= 1
        assert self.state == state, f'Cannot set disclosure triangle to state: "{state}"'

    state = property(get_state, set_state)


class MenuItem(BaseUIElement):
    @property
    def is_enabled(self):
        return wait_condition(self._is_enabled)


class MenuBarItem(BaseUIElement):
    pass


class Menu(BaseUIElement):
    pass


class Group(BaseUIElement):
    @property
    def elements_number(self):
        return self._count_elements()


class Row(BaseUIElement):
    def select(self, pause: float = 0.3):
        self._select()
        time.sleep(pause)

    @property
    def is_selected(self) -> bool:
        return self._read_attribute('AXSelected')


class ScrollArea(BaseUIElement):
    pass


class Table(BaseUIElement):
    @property
    def rows_number(self) -> int:
        return self._rows


class Image(BaseUIElement):
    @property
    def label(self):
        return self.description


class List(BaseUIElement):
    @property
    def elements_number(self):
        return self._count_elements()


class Outline(BaseUIElement):
    @property
    def elements_number(self):
        return self._count_elements()


class Popover(BaseUIElement):
    pass


class Sheet(BaseUIElement):
    pass


class Window(BaseUIElement):
    def __init__(self, locator, process):
        super().__init__(locator, process)

    def set_minimized(self, value):
        converted = {True: 'true', False: 'false'}.get(value)
        self._set_attribute('AXMinimized', converted)

    def is_minimized(self):
        return self._read_attribute('AXMinimized')

    def set_full_screen(self, value):
        converted = {True: 'true', False: 'false'}.get(value)
        self._set_attribute('AXFrontmost', converted)

    def is_full_screen(self):
        return self._read_attribute('AXFullScreen')

    @property
    def is_keyboard_focused(self) -> bool:
        return self._read_attribute('AXFocused')

    minimized = property(is_minimized, set_minimized)
    full_screen = property(is_full_screen, set_full_screen)


class WebView(BaseUIElement):
    @property
    def url(self):
        wait_condition(lambda: self._read_attribute('AXURL') is not None, timeout=60)
        wait_condition(lambda: self._read_attribute('AXURL').startswith('http'), timeout=30)
        return wait_condition(lambda: self._read_attribute('AXURL'), timeout=30)


@dataclass(frozen=True)
class Elements:
    all: MappingProxyType = MappingProxyType(
        {'UI element': BaseUIElement, 'button': Button, 'pop up button': Button, 'radio button': Button,
            'busy indicator': BusyIndicator, 'static text': StaticText, 'text area': TextArea, 'text field': TextField,
            'checkbox': Checkbox, 'combo box': ComboBox, 'menu item': MenuItem, 'menu button': MenuItem,
            'menu bar item': MenuBarItem, 'menu': Menu, 'group': Group, 'row': Row, 'scroll area': ScrollArea,
            'table': Table, 'image': Image, 'list': List, 'outline': Outline, 'pop over': Popover, 'popover': Popover,
            'sheet': Sheet, 'window': Window, })


class ASElement:
    """AppleScript element factory."""
    __slots__ = ()
    window: str = 'of window 1'

    def __new__(cls, locator: str, process: str) \
            -> Union[BaseUIElement, Button, BusyIndicator, TextArea, TextField, Checkbox, ComboBox, MenuItem,
                     Group, Row, ScrollArea, Table, Image, List, Outline, Popover, Sheet, Window]:
        locator = locator.replace('of of', 'of')
        return cls.__define_locator_type(locator)(locator, process)

    @staticmethod
    def __define_locator_type(locator: str):
        _l = locator.split(' of')[0]
        _l = (''.join((i for i in _l if not i.isdigit())) if _l[-1].isdigit() else _l.split('"')[0]).strip()
        return Elements.all.get(_l, BaseUIElement)
