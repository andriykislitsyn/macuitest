import time
from typing import Tuple

import AppKit
import Quartz

from macuitest.lib.elements.ui.monitor import monitor

# Cursor updates per second during a move, above typical display refresh rates.
MOVE_EVENTS_PER_SECOND = 120


class MouseController:
    def move_to(self, x: float, y: float, duration: float = 0.35):
        self.__mouse_move_drag(x=x, y=y, duration=duration)
        time.sleep(0.125)

    def drag_to(self, x: float, y: float, duration: float = 0.35):
        self.__mouse_move_drag(x=x, y=y, duration=duration, move="drag")
        time.sleep(0.125)

    def mouse_down(self, x: float, y: float, button: str):
        if button == "left":
            self._send_mouse_event(Quartz.kCGEventLeftMouseDown, x, y, Quartz.kCGMouseButtonLeft)
        elif button == "middle":
            self._send_mouse_event(Quartz.kCGEventOtherMouseDown, x, y, Quartz.kCGMouseButtonCenter)
        elif button == "right":
            self._send_mouse_event(Quartz.kCGEventRightMouseDown, x, y, Quartz.kCGMouseButtonRight)
        else:
            raise ValueError("button argument not in ('left', 'middle', 'right')")

    def mouse_up(self, x: float, y: float, button: str):
        if button == "left":
            self._send_mouse_event(Quartz.kCGEventLeftMouseUp, x, y, Quartz.kCGMouseButtonLeft)
        elif button == "middle":
            self._send_mouse_event(Quartz.kCGEventOtherMouseUp, x, y, Quartz.kCGMouseButtonCenter)
        elif button == "right":
            self._send_mouse_event(Quartz.kCGEventRightMouseUp, x, y, Quartz.kCGMouseButtonRight)
        else:
            raise ValueError("button argument not in ('left', 'middle', 'right')")

    def __mouse_move_drag(self, x: float, y: float, duration: float, move: str = "move"):
        kcg_event, mouse_button = Quartz.kCGEventMouseMoved, 0
        if move == "drag":
            kcg_event, mouse_button = Quartz.kCGEventLeftMouseDragged, Quartz.kCGMouseButtonLeft
        start_x, start_y = self.position
        bounds = monitor.bounds
        # Keep the target on the virtual desktop, which spans every connected display.
        x = max(bounds.x1, min(x, bounds.x2 - 1))
        y = max(bounds.y1, min(y, bounds.y2 - 1))
        steps = max(1, round(duration * MOVE_EVENTS_PER_SECOND))
        start = time.perf_counter()
        for n in range(1, steps + 1):
            # Sleep until this step's slot, so time spent posting events doesn't stretch the move.
            time.sleep(max(0.0, start + duration * n / steps - time.perf_counter()))
            fraction = ease_out_quad(n / steps)
            point = (x, y) if n == steps else get_point_on_line(start_x, start_y, x, y, fraction)
            self._send_mouse_event(kcg_event, *point, mouse_button)

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
    def multi_click(x: float, y: float, button: str, clicks: int):
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

    @staticmethod
    def _send_mouse_event(event, x: float, y: float, button):
        event = Quartz.CGEventCreateMouseEvent(None, event, (x, y), button)
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, event)


def ease_out_quad(n: float) -> float:
    """A quadratic tween function that begins fast and then decelerates."""
    return -n * (n - 2)


def get_point_on_line(x1: float, y1: float, x2: float, y2: float, n: float) -> Tuple[float, float]:
    """Return point that has progressed a proportion n
    along the line defined by the two x, y coordinates."""
    return ((x2 - x1) * n) + x1, ((y2 - y1) * n) + y1
