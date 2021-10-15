import time
from dataclasses import dataclass

from macuitest.lib.elements.controllers.keyboard_controller import keyboard
from macuitest.lib.elements.controllers.mouse_controller import MouseController


@dataclass(frozen=True)
class MouseConfig:
    """Mouse options."""

    move: float = 0.18  # Cursor roaming time.
    hold: float = 0.24  # Time to hold a button selected.
    pause: float = 0.24  # Pause after an action.
    default_position: tuple = (5, 3)


class Mouse:
    """Cursor manipulator."""

    def __init__(self, controller: MouseController):
        self.controller = controller

    def paste(self, x: int, y: int, phrase: str = "") -> None:
        """Hover over the position and click once. Then paste `phrase` from clipboard."""
        self.click(x, y)
        keyboard.write(phrase, pause=0.02)

    def double_click(
        self, x: int, y: int, _x: int = 0, _y: int = 0, duration: float = MouseConfig.move
    ) -> None:
        """Hover over position and click twice."""
        self.hover(x, y, duration=duration)
        self.controller.multi_click(x, y, button="left", clicks=2)

    def drag(self, x1: int, y1: int, x2: int, y2: int) -> None:
        self.hover(x1, y1)
        self.controller.mouse_down(x1, y1, "left")
        time.sleep(0.5)
        self.controller.drag_to(x2, y2)
        time.sleep(0.5)
        self.controller.mouse_up(x2, y2, "left")
        time.sleep(0.25)

    def click(
        self,
        x: int,
        y: int,
        hold: float = MouseConfig.hold,
        duration: float = MouseConfig.move,
        pause: float = MouseConfig.pause,
    ) -> None:
        """Hover over position and left-click once."""
        time.sleep(pause)
        self.hover(x, y, duration)
        self._press_mouse_button(x, y, mouse_button="left", hold=hold, pause=0.125)

    def right_click(
        self,
        x: int,
        y: int,
        hold: float = MouseConfig.hold,
        duration: float = MouseConfig.move,
        pause: float = MouseConfig.pause,
    ) -> None:
        """Hover over the position and control-click once."""
        time.sleep(pause)
        self.hover(x, y, duration)
        self._press_mouse_button(x, y, mouse_button="right", hold=hold, pause=0.125)

    def scroll(self, x: int, y: int, scrolls: int = 1) -> None:
        self.hover(x, y)
        self.controller.vertical_scroll(scrolls)

    def reset(self):
        self.hover(*MouseConfig.default_position)

    def hover(self, x: int, y: int, duration: float = MouseConfig.move) -> None:
        """Hover over the position."""
        self.controller.move_to(x, y, duration=duration)

    def _press_mouse_button(self, x: int, y: int, mouse_button: str, hold: float, pause: float):
        time.sleep(pause)
        self.controller.mouse_down(x, y, mouse_button)
        time.sleep(hold)
        self.controller.mouse_up(x, y, mouse_button)
        time.sleep(0.25)  # We want to wait a bit for system to register the event.


mouse = Mouse(MouseController())
