import math
import time
from dataclasses import dataclass
from datetime import datetime
from types import MappingProxyType
from typing import Any
from typing import List
from typing import Optional
from typing import Tuple
from typing import Union

from macuitest.config.constants import CheckboxState
from macuitest.config.constants import DisclosureTriangleState
from macuitest.config.constants import Frame
from macuitest.config.constants import Point
from macuitest.config.constants import Region
from macuitest.lib import core
from macuitest.lib.applescript_lib.applescript_wrapper import AppleScriptError
from macuitest.lib.applescript_lib.applescript_wrapper import as_wrapper
from macuitest.lib.core import is_close
from macuitest.lib.core import wait_condition
from macuitest.lib.elements.controllers.keyboard_controller import keyboard
from macuitest.lib.elements.controllers.mouse import MouseConfig
from macuitest.lib.elements.controllers.mouse import mouse
from macuitest.lib.elements.ui.monitor import monitor
from macuitest.lib.operating_system.color_meter import get_color
from macuitest.lib.operating_system.color_meter import get_most_common_color
from macuitest.lib.operating_system.env import env


class BaseUIElement:
    """Represent a UI element based on an AppleScript locator."""

    __slots__ = ("locator", "process", "_frame")

    def __init__(self, locator: str, process: str):
        self.locator = locator
        self.process = process

    def __repr__(self):
        return f'<{self.__class__.__name__} "{self.locator}", process="{self.process}">'

    def wait_on_position(self, position: Point) -> bool:
        for _ in range(50):
            f = self.frame
            if is_close(f.center.x, position.x, threshold=2) and is_close(
                f.center.y, position.y, threshold=2
            ):
                return True
            time.sleep(0.1)

    def snapshot(self, margin: int = 4) -> str:
        frame = self.frame
        element_region = (
            frame.x1 - margin,
            frame.y1 - margin,
            frame.width + margin * 2,
            frame.height + margin * 2,
        )
        return monitor.save_screenshot(
            region=element_region,
            where=f'{env.desktop}/scr_{datetime.now().strftime("%Y%m%d%H%M%S%f")}.png',
        )

    @property
    def region(self):
        return self.get_region()

    def get_region(self, margin: int = 0) -> Region:
        f = self.frame
        return Region(f.x1 - margin, f.y1 - margin, f.x2 + margin, f.y2 + margin)

    def most_common_color(self, ignore_colors: Optional[Tuple[str, ...]] = None):
        f = self.frame
        return get_most_common_color(f.x1, f.x2, f.y1, f.y2, ignore_colors)

    def color(self, x_off: int = 0, y_off: int = 0) -> str:
        c = self.frame.center
        return get_color(Point(c.x + x_off, c.y + y_off)).replace("gray", "grey")

    def scroll(self, x_off: int = 0, y_off: int = 0, clicks: int = 1):
        c = self.frame.center
        mouse.scroll(c.x + x_off, c.y + y_off, scrolls=clicks)

    def doubleclick_mouse(self, x_off: int = 0, y_off: int = 0, duration: float = MouseConfig.move):
        c = self.frame.center
        mouse.double_click(c.x + x_off, c.y + y_off, duration=duration)

    def rightclick_mouse(
        self,
        x_off: int = 0,
        y_off: int = 0,
        hold: float = MouseConfig.hold,
        duration: float = MouseConfig.move,
        pause: float = MouseConfig.pause,
    ) -> None:
        c = self.frame.center
        mouse.right_click(c.x + x_off, c.y + y_off, hold, duration, pause)

    def click_mouse(
        self,
        x_off: int = 0,
        y_off: int = 0,
        hold: float = MouseConfig.hold,
        duration: float = MouseConfig.move,
        pause: float = MouseConfig.pause,
    ) -> None:
        c = self.frame.center
        mouse.click(c.x + x_off, c.y + y_off, hold, duration, pause)

    def hover_mouse(
        self, x_off: int = 0, y_off: int = 0, duration: float = MouseConfig.move
    ) -> None:
        c = self.frame.center
        mouse.hover(c.x + x_off, c.y + y_off, duration=duration)

    @property
    def frame(self) -> Frame:
        self.__assert_visible()
        _frame = (*self.get_attribute_value("AXPosition"), *self.get_attribute_value("AXSize"))
        x1, y1, width, height = (math.floor(x) for x in _frame)
        x2, y2 = x1 + width, y1 + height
        center = Point(int((x1 + width / 2)), int((y1 + height / 2)))
        return Frame(x1, y1, x2, y2, center, width, height)

    def click(self, pause: float = 0.4) -> bool:
        """Perform click action the element."""
        self.__assert_visible()
        time.sleep(pause)
        self._execute("click")
        time.sleep(0.25)
        return True

    def _select(self):
        """Click an element."""
        self.__assert_visible()
        return self._execute("select")

    def _set_focus(self, value):
        """Make element focused."""
        self.__assert_visible()
        return self._execute("set focused of", params=f'to "{value}"')

    def _show_context_menu(self):
        self.__assert_visible()
        return self._execute('perform action "AXShowMenu" of')

    def _set_value(self, value):
        """Set element value."""
        self.__assert_visible()
        return self._execute("set value of", params=f'to "{value}"')

    def _get_value(self):
        """Get element value."""
        self.__assert_visible()
        return self._execute("get value of")

    def _count_elements(self) -> int:
        """Count UI elements"""
        self.__assert_visible()
        return self._execute("count UI elements of")

    @property
    def _children(self):
        self.__assert_visible()
        return self.get_attribute_value("AXChildren")

    @property
    def _rows(self) -> int:
        self.__assert_visible()
        return self._execute("count rows of")

    @property
    def title(self) -> str:
        self.__assert_visible()
        return self.get_attribute_value("AXTitle").strip()

    @property
    def description(self) -> str:
        self.__assert_visible()
        return self.get_attribute_value("AXDescription").strip()

    @property
    def value(self) -> str:
        self.__assert_visible()
        return self.get_attribute_value("AXValue")

    @property
    def help(self) -> str:
        self.__assert_visible()
        return self.get_attribute_value("AXHelp")

    @property
    def _placeholder(self) -> str:
        self.__assert_visible()
        return self.get_attribute_value("AXPlaceholderValue")

    def _is_enabled(self) -> bool:
        """Check whether element enabled"""
        self.__assert_visible()
        return self.get_attribute_value("AXEnabled")

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

    def perform_action(self, action):
        self._execute(f'perform action "{action}" of')

    @property
    def actions(self) -> List[str]:
        try:
            return self._execute("get name of every action of")
        except AppleScriptError:
            return []

    def _set_attribute(self, attribute, value) -> Any:
        return self._execute(f'set value of attribute "{attribute}" of', params=f"to {value}")

    def get_attribute_value(self, attribute) -> Any:
        try:
            return self._execute(f'get value of attribute "{attribute}" of')
        except AppleScriptError:
            return None

    @property
    def attributes(self) -> List[str]:
        try:
            return self._execute("get name of every attribute of")
        except AppleScriptError:
            return []

    def is_exists(self) -> bool:
        try:
            return self._execute("return exists")
        except AppleScriptError as e:
            if e.number == -10000:
                pass
            else:
                raise

    def __assert_visible(self):
        if not self.is_visible:
            raise LookupError(self)

    def _execute(self, command: str, params: str = ""):
        """Execute a command.
        :param str command: The name of the command to _execute as a string.
        :param str params: Command parameters.
        :return str: Execution output."""
        _command = f"{command} {self.locator} {params}" if params else f"{command} {self.locator}"
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
        return self.get_attribute_value("AXNumberOfCharacters")

    @property
    def visible_characters_number(self):
        return list(self.get_attribute_value("AXVisibleCharacterRange"))[1]

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


class TextField(TextElement):
    def fill(self, with_text: str, pause: float = 0.01):
        for _ in range(2):
            self.text = ""
            self.focus()
            time.sleep(0.5)
            keyboard.write(with_text, pause=pause)
            if wait_condition(lambda: len(self.text) == len(with_text), timeout=0.5):
                break
        if not len(self.text) == len(with_text):
            raise KeyboardInterrupt(f'"{with_text}" expected but "{self.text}" received.')

    def focus(self, value="true"):
        self._set_focus(value)

    @property
    def is_secure(self) -> bool:
        return self.get_attribute_value("AXRoleDescription") == "secure text field"

    @property
    def placeholder(self):
        return self._placeholder

    def __get_value(self) -> str:
        return self._get_value()

    def __set_value(self, value):
        self._set_value(str(value))

    def __get_focused(self):
        return self.get_attribute_value("AXFocused")

    def __set_focused(self, value: bool):
        self._set_focus(value)

    is_focused = property(__get_focused, __set_focused)
    text = property(__get_value, __set_value)


class TextArea(TextField):
    pass


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
        if self.state != target_state:
            raise EnvironmentError(f'Cannot set checkbox to state: "{state}"')

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
        if self.state != state:
            raise EnvironmentError(f'Cannot set disclosure triangle to state: "{state}"')

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
        return self.get_attribute_value("AXSelected")


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


class _List(BaseUIElement):
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

    def set_position(self, point: Tuple[int, int]):
        self._execute("set position of", params="to {%s, %s}" % (point[0], point[1]))

    def get_position(self) -> Tuple[int, int]:
        return tuple(self._execute("get position of"))

    def set_size(self, size: Tuple[int, int]):
        self._execute("set size of", params="to {%s, %s}" % (size[0], size[1]))

    def get_size(self) -> Tuple[int, int]:
        return tuple(self._execute("get size of"))

    def set_minimized(self, value):
        converted = {True: "true", False: "false"}.get(value)
        self._set_attribute("AXMinimized", converted)

    def is_minimized(self):
        return self.get_attribute_value("AXMinimized")

    def set_full_screen(self, value):
        converted = {True: "true", False: "false"}.get(value)
        self._set_attribute("AXFrontmost", converted)

    def is_full_screen(self):
        return self.get_attribute_value("AXFullScreen")

    @property
    def is_keyboard_focused(self) -> bool:
        return self.get_attribute_value("AXFocused")

    position = property(get_position, set_position)
    size = property(get_size, set_size)
    minimized = property(is_minimized, set_minimized)
    full_screen = property(is_full_screen, set_full_screen)


class WebView(BaseUIElement):
    @property
    def url(self):
        wait_condition(lambda: self.get_attribute_value("AXURL") is not None, timeout=60)
        wait_condition(lambda: self.get_attribute_value("AXURL").startswith("http"), timeout=30)
        return wait_condition(lambda: self.get_attribute_value("AXURL"), timeout=30)


@dataclass(frozen=True)
class Elements:
    all: MappingProxyType = MappingProxyType(
        {
            "UI element": BaseUIElement,
            "button": Button,
            "pop up button": Button,
            "radio button": Button,
            "busy indicator": BusyIndicator,
            "static text": StaticText,
            "text area": TextArea,
            "text field": TextField,
            "checkbox": Checkbox,
            "combo box": ComboBox,
            "menu item": MenuItem,
            "menu button": MenuItem,
            "menu bar item": MenuBarItem,
            "menu": Menu,
            "group": Group,
            "row": Row,
            "scroll area": ScrollArea,
            "table": Table,
            "image": Image,
            "list": _List,
            "outline": Outline,
            "pop over": Popover,
            "popover": Popover,
            "sheet": Sheet,
            "window": Window,
        }
    )


class ASElement:
    """AppleScript element factory."""

    def __new__(
        cls, locator: str, process: str
    ) -> Union[
        BaseUIElement,
        Button,
        BusyIndicator,
        TextArea,
        TextField,
        Checkbox,
        ComboBox,
        MenuItem,
        Group,
        Row,
        ScrollArea,
        Table,
        Image,
        List,
        Outline,
        Popover,
        Sheet,
        Window,
    ]:
        loc = locator.split(" of")[0]
        loc = (
            "".join((i for i in loc if not i.isdigit())) if loc[-1].isdigit() else loc.split('"')[0]
        ).strip()
        return Elements.all.get(loc, BaseUIElement)(locator, process)
