from typing import Union, Optional

import cv2
import numpy

from macuitest.config.constants import Point, Region
from macuitest.lib.core import wait_condition
from macuitest.lib.elements.controllers.mouse import mouse
from macuitest.lib.ui.monitor import monitor
from macuitest.lib.ui.opencv_wrapper import opencv_wrapper


class UIElementNotFoundOnScreen(Exception):
    """Thrown when a pattern is not found on the screen."""
    pass


class UIElement:
    """Represent a visible user interface element. Based on automated pattern recognition algorithm (OpenCV)."""

    def __init__(self, scr_path: str, sim: float = 0.85):
        self.pattern = scr_path.strip()
        self.similarity = sim
        self.image, self.width, self.height = None, None, None
        self._center = None
        self.load_image()

    def __repr__(self):
        return f"{self.__class__.__name__}(pattern='..{self.short_name}', sim={self.similarity})"

    @property
    def short_name(self):
        return self.pattern.split('media')[-1]

    def paste(self, x_off=0, y_off=0, phrase=''):
        mouse.paste(self.center.x, self.center.y, x_off, y_off, phrase=phrase)
        self._center = None

    def double_click(self, x_off=0, y_off=0):
        mouse.double_click(self.center.x, self.center.y, x_off, y_off)
        self._center = None

    def right_click(self, x_off=0, y_off=0):
        mouse.right_click(self.center.x, self.center.y, x_off, y_off)
        self._center = None

    def click(self, x_off=0, y_off=0, hold=.3):
        mouse.click(self.center.x, self.center.y, x_off, y_off, hold=hold)
        self._center = None

    def hover_above(self, x_off=0, y_off=0, duration=.2):
        mouse.hover(self.center.x, self.center.y, x_off, y_off, duration=duration)
        self._center = None

    @property
    def is_visible(self):
        return self.wait_displayed() is not None

    @property
    def center(self):
        match = self._center or self.wait_displayed()
        if not match:
            raise UIElementNotFoundOnScreen(self.short_name)
        return Point(match.x + self.width / 2, match.y + self.height / 2)

    def wait_displayed(self, timeout=5, region: Optional[Region] = None) -> Union[None, Point]:
        match = wait_condition(
            lambda: opencv_wrapper.find_pattern(self.image, self.similarity, region), timeout=timeout)
        if isinstance(match, Point):
            self._center = match
            return match

    def wait_vanish(self, timeout=30, region: Optional[Region] = None) -> bool:
        return wait_condition(
            lambda: opencv_wrapper.find_pattern(self.image, self.similarity, region) is None,  timeout=timeout)

    def load_image(self) -> numpy.ndarray:
        image = cv2.imread(self.pattern, 0)
        if image is None:
            return numpy.empty(2)
        height, width = image.shape
        if monitor.is_retina:
            height, width = height / 2, width / 2
        self.image, self.width, self.height = image, width, height
