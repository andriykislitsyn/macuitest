import time
from typing import Tuple

import AppKit
import Quartz


class MouseController:
    def __init__(self):
        self.__screen_size = None

    def move_to(self, x: int, y: int, duration: float = 0.35):
        self.__mouse_move_drag(x=x, y=y, duration=duration)
        time.sleep(0.125)

    def drag_to(self, x: int, y: int, duration: float = 0.35):
        self.__mouse_move_drag(x=x, y=y, duration=duration, move="drag")
        time.sleep(0.125)

    def mouse_down(self, x: int, y: int, button: str):
        if button == "left":
            self._send_mouse_event(Quartz.kCGEventLeftMouseDown, x, y, Quartz.kCGMouseButtonLeft)
        elif button == "middle":
            self._send_mouse_event(Quartz.kCGEventOtherMouseDown, x, y, Quartz.kCGMouseButtonCenter)
        elif button == "right":
            self._send_mouse_event(Quartz.kCGEventRightMouseDown, x, y, Quartz.kCGMouseButtonRight)
        else:
            raise ValueError("button argument not in ('left', 'middle', 'right')")

    def mouse_up(self, x: int, y: int, button: str):
        if button == "left":
            self._send_mouse_event(Quartz.kCGEventLeftMouseUp, x, y, Quartz.kCGMouseButtonLeft)
        elif button == "middle":
            self._send_mouse_event(Quartz.kCGEventOtherMouseUp, x, y, Quartz.kCGMouseButtonCenter)
        elif button == "right":
            self._send_mouse_event(Quartz.kCGEventRightMouseUp, x, y, Quartz.kCGMouseButtonRight)
        else:
            raise ValueError("button argument not in ('left', 'middle', 'right')")

    def __mouse_move_drag(self, x: int, y: int, duration: float, move: str = "move"):
        kcg_event, mouse_button = Quartz.kCGEventMouseMoved, 0
        if move == "drag":
            kcg_event, mouse_button = Quartz.kCGEventLeftMouseDragged, Quartz.kCGMouseButtonLeft
        start_x, start_y = self.position
        width, height = self.screen_size
        x = max(0, min(x, width - 1))  # Make sure x and y are within the screen bounds.
        y = max(0, min(y, height - 1))
        steps_count = int(max(abs(x - start_x), abs(y - start_y))) or 1
        if steps_count < 50:
            duration /= 3
        pause = duration / steps_count
        for step in (
            get_point_on_line(start_x, start_y, x, y, ease_out_quad(n / steps_count))
            for n in range(steps_count)
        ):
            self._send_mouse_event(kcg_event, *step, mouse_button)
            time.sleep(pause)
        self._send_mouse_event(kcg_event, x, y, mouse_button)

    @staticmethod
    def vertical_scroll(scrolls: int, speed: int = 1):
        if scrolls < 0:
            speed *= -1
        for _ in range(abs(scrolls)):
            swe = Quartz.CGEventCreateScrollWheelEvent(
                None, Quartz.kCGScrollEventUnitLine, 1, speed
            )
            Quartz.CGEventPost(Quartz.kCGHIDEventTap, swe)
            time.sleep(0.003)

    @staticmethod
    def multi_click(x: int, y: int, button: str, clicks: int):
        if button == "left":
            btn = Quartz.kCGMouseButtonLeft
            down = Quartz.kCGEventLeftMouseDown
            up = Quartz.kCGEventLeftMouseUp
        elif button == "middle":
            btn = Quartz.kCGMouseButtonCenter
            down = Quartz.kCGEventOtherMouseDown
            up = Quartz.kCGEventOtherMouseUp
        elif button == "right":
            btn = Quartz.kCGMouseButtonRight
            down = Quartz.kCGEventRightMouseDown
            up = Quartz.kCGEventRightMouseUp
        else:
            raise ValueError("button argument not in ('left', 'middle', 'right')")

        mouse_event = Quartz.CGEventCreateMouseEvent(None, down, (x, y), btn)
        Quartz.CGEventSetIntegerValueField(mouse_event, Quartz.kCGMouseEventClickState, clicks)
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, mouse_event)
        Quartz.CGEventSetType(mouse_event, up)
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, mouse_event)
        for _ in range(clicks - 1):
            Quartz.CGEventSetType(mouse_event, down)
            Quartz.CGEventPost(Quartz.kCGHIDEventTap, mouse_event)
            Quartz.CGEventSetType(mouse_event, up)
            Quartz.CGEventPost(Quartz.kCGHIDEventTap, mouse_event)

    @property
    def position(self):
        # noinspection PyUnresolvedReferences
        loc = AppKit.NSEvent.mouseLocation()
        return int(loc.x), int(Quartz.CGDisplayPixelsHigh(0) - loc.y)

    @property
    def screen_size(self):
        if self.__screen_size is None:
            display = Quartz.CGMainDisplayID()
            self.__screen_size = Quartz.CGDisplayPixelsWide(display), Quartz.CGDisplayPixelsHigh(
                display
            )
        return self.__screen_size

    @staticmethod
    def _send_mouse_event(event, x: int, y: int, button):
        event = Quartz.CGEventCreateMouseEvent(None, event, (x, y), button)
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, event)


def ease_out_quad(n: float) -> float:
    """A quadratic tween function that begins fast and then decelerates."""
    return -n * (n - 2)


def get_point_on_line(x1: int, y1: int, x2: int, y2: int, n: float) -> Tuple[float, float]:
    """Return point that has progressed a proportion n
    along the line defined by the two x, y coordinates."""
    return ((x2 - x1) * n) + x1, ((y2 - y1) * n) + y1
