import time
from dataclasses import dataclass
from typing import Union

import pyautogui


@dataclass
class _Options:
    """Mouse options."""
    move_time: Union[float, int] = .2
    hold_time: float = .3
    pause: float = .3
    default_position: tuple = (28, 30)
    tween = pyautogui.easeInExpo


class Mouse:
    """Cursor manipulator."""

    def click(self, x, y, _x=0, _y=0, hold=_Options.hold_time, duration=_Options.move_time, pause=_Options.pause):
        """Hover over position and left-click once."""
        self.hover(x + _x, y + _y, duration)
        self._press_mouse_button(mouse_button='left', hold=hold, pause=pause)

    def paste(self, x, y, _x=0, _y=0, phrase=''):
        """Hover over the position and click once. Then paste `phrase` from clipboard."""
        self.double_click(x + _x, y + _y)
        pyautogui.typewrite(phrase, interval=0.01)

    def double_click(self, x, y, _x=0, _y=0, duration=_Options.move_time):
        """Hover over position and click twice."""
        self.hover(x, y, _x, _y, duration=duration)
        pyautogui.doubleClick()

    def right_click(self, x, y, _x=0, _y=0, duration=_Options.move_time, pause=_Options.pause):
        """Hover over the position and control-click once."""
        self.hover(x + _x, y + _y, duration)
        pyautogui.rightClick(pause=pause)

    def scroll(self, x, y, clicks, _x=0, _y=0):
        self.hover(x, y, _x, _x)
        pyautogui.scroll(clicks)

    def reset(self, state=False):
        pyautogui.FAILSAFE = state  # Set PyAutoGUI's fail-safe check state.
        self.hover(*_Options.default_position, duration=0.03)

    @staticmethod
    def _press_mouse_button(mouse_button: str, hold: float = _Options.hold_time, pause: float = _Options.pause):
        pyautogui.mouseDown(button=mouse_button)
        time.sleep(hold)
        pyautogui.mouseUp(button=mouse_button)
        time.sleep(pause)

    @staticmethod
    def hover(x: int, y: int, _x: int = 0, _y: int = 0, duration: float = _Options.move_time) -> None:
        """Hover over the position."""
        pyautogui.moveTo(x + _x, y + _y, duration=duration, tween=_Options.tween)


mouse = Mouse()
