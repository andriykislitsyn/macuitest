import time
from dataclasses import dataclass
from typing import Optional

from macuitest.lib.elements.controllers.keyboard_controller import keyboard
from macuitest.lib.elements.controllers.mouse_controller import MouseController


@dataclass
class MouseConfig:
    """Mouse timings in seconds, read on every call. Change them with `MouseConfig.move = 0.36`."""

    move: float = 0.18  # Cursor roaming time.
    hold: float = 0.24  # Time to hold a button selected.
    pause: float = 0.24  # Pause after an action.
    default_position: tuple = (5, 3)


class Mouse:
    """Cursor manipulator."""

    def __init__(self, controller: MouseController):
        self.controller = controller

    def paste(self, x: float, y: float, phrase: str = "") -> None:
        """Hover over the position and click once. Then paste `phrase` from clipboard."""
        self.click(x, y)
        keyboard.write(phrase, pause=0.02)

    def double_click(
        self, x: float, y: float, _x: int = 0, _y: int = 0, duration: Optional[float] = None
    ) -> None:
        """Hover over position and click twice."""
        self.hover(x, y, duration=duration)
        self.controller.multi_click(x, y, button="left", clicks=2)

    def drag(self, x1: float, y1: float, x2: float, y2: float) -> None:
        self.hover(x1, y1)
        self.controller.mouse_down(x1, y1, "left")
        time.sleep(0.5)
        self.controller.drag_to(x2, y2)
        time.sleep(0.5)
        self.controller.mouse_up(x2, y2, "left")
        time.sleep(0.25)

    def click(
        self,
        x: float,
        y: float,
        hold: Optional[float] = None,
        duration: Optional[float] = None,
        pause: Optional[float] = None,
    ) -> None:
        """Hover over position and left-click once."""
        time.sleep(MouseConfig.pause if pause is None else pause)
        self.hover(x, y, duration)
        self._press_mouse_button(x, y, mouse_button="left", hold=hold, pause=0.125)

    def right_click(
        self,
        x: float,
        y: float,
        hold: Optional[float] = None,
        duration: Optional[float] = None,
        pause: Optional[float] = None,
    ) -> None:
        """Hover over the position and control-click once."""
        time.sleep(MouseConfig.pause if pause is None else pause)
        self.hover(x, y, duration)
        self._press_mouse_button(x, y, mouse_button="right", hold=hold, pause=0.125)

    def scroll(self, x: float, y: float, scrolls: int = 1) -> None:
        self.hover(x, y)
        self.controller.vertical_scroll(scrolls)

    def reset(self):
        self.hover(*MouseConfig.default_position)

    def hover(self, x: float, y: float, duration: Optional[float] = None) -> None:
        """Hover over the position."""
        self.controller.move_to(x, y, duration=MouseConfig.move if duration is None else duration)

    def _press_mouse_button(
        self, x: float, y: float, mouse_button: str, hold: Optional[float], pause: float
    ):
        time.sleep(pause)
        self.controller.mouse_down(x, y, mouse_button)
        time.sleep(MouseConfig.hold if hold is None else hold)
        self.controller.mouse_up(x, y, mouse_button)
        time.sleep(0.25)  # We want to wait a bit for system to register the event.


mouse = Mouse(MouseController())
