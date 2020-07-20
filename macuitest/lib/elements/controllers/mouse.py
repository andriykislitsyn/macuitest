import time
from dataclasses import dataclass

from macuitest.lib.elements.controllers.keyboard_controller import KeyBoardController
from macuitest.lib.elements.controllers.mouse_controller import MouseController


@dataclass(frozen=True)
class Options:
    """Mouse options."""
    move: float = .25  # Cursor roaming time.
    hold: float = .25  # Time to hold a button selected.
    pause: float = .25  # Pause after an action.
    default_position: tuple = (28, 30)


class Mouse:
    """Cursor manipulator."""

    def __init__(self, controller: MouseController):
        self.controller = controller

    def double_click(self, x, y, _x=0, _y=0, duration=Options.move):
        """Hover over position and click twice."""
        self.click(x, y, _x, _y, duration=duration)
        self.controller.multi_click(x + _x, y + _y, button='left', clicks=2)

    def drag(self, x1: int, y1: int, x2: int, y2: int):
        self.hover(x1, y1)
        self.controller.mouse_down(x1, y1, 'left')
        self.controller.drag_to(x2, y2)
        self.controller.mouse_up(x2, y2, 'left')

    def click(self, x, y, _x=0, _y=0, hold=Options.hold, duration=Options.move, pause=Options.pause):
        """Hover over position and left-click once."""
        self.hover(x, y, _x, _y, duration)
        self._press_mouse_button(x + _x, y + _y, mouse_button='left', hold=hold, pause=pause)

    def right_click(self, x, y, _x=0, _y=0, hold=Options.hold, duration=Options.move, pause=Options.pause):
        """Hover over the position and control-click once."""
        self.hover(x, y, _x, _y, duration)
        self._press_mouse_button(x + _x, y + _y, mouse_button='right', hold=hold, pause=pause)

    def paste(self, x, y, _x=0, _y=0, phrase=''):
        """Hover over the position and click once. Then paste `phrase` from clipboard."""
        self.double_click(x + _x, y + _y)
        time.sleep(.5)
        KeyBoardController().write(phrase, pause=.005)

    def scroll(self, x, y, scrolls, _x=0, _y=0):
        self.hover(x, y, _x, _x)
        self.controller.vertical_scroll(scrolls)

    def reset(self):
        self.hover(*Options.default_position, duration=0.03)

    def hover(self, x: int, y: int, _x: int = 0, _y: int = 0, duration: float = Options.move) -> None:
        """Hover over the position."""
        self.controller.move_to(x + _x, y + _y, duration=duration)

    def _press_mouse_button(self, x: int, y: int, mouse_button: str, hold: float, pause: float):
        self.controller.mouse_down(x, y, mouse_button)
        time.sleep(hold)
        self.controller.mouse_up(x, y, mouse_button)
        time.sleep(pause)


mouse = Mouse(MouseController())
