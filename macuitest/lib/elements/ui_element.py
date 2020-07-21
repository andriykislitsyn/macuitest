from pathlib import Path
from typing import Union, Optional

import cv2

from macuitest.config.constants import Point, Region
from macuitest.lib.core import wait_condition
from macuitest.lib.elements.controllers.mouse import mouse
from macuitest.lib.elements.ui.monitor import monitor


class UIElementNotFoundOnScreen(Exception):
    """Thrown when a pattern is not found on the screen."""
    pass


class UIElement:
    """Represent a visible user interface element. Based on automated pattern recognition algorithm (OpenCV)."""

    def __init__(self, screenshot_path: str, similarity: float = 0.85):
        self.path = screenshot_path.strip()
        self.similarity = similarity
        self.image, self.width, self.height = None, None, None
        self.__center: Optional[Point] = None
        self.load_image()

    def __repr__(self):
        return f'<UIElement "{self.path}", sim={self.similarity}>'

    def paste(self, x_off=0, y_off=0, phrase=''):
        mouse.paste(self.center.x, self.center.y, x_off, y_off, phrase=phrase)
        self.__center = None

    def double_click(self, x_off=0, y_off=0):
        mouse.double_click(self.center.x, self.center.y, x_off, y_off)
        self.__center = None

    def right_click(self, x_off=0, y_off=0):
        mouse.right_click(self.center.x, self.center.y, x_off, y_off)
        self.__center = None

    def click_mouse(self, x_off=0, y_off=0, hold=.3):
        mouse.click(self.center.x, self.center.y, x_off, y_off, hold=hold)
        self.__center = None

    def hover_mouse(self, x_off=0, y_off=0, duration=.2):
        mouse.hover(self.center.x, self.center.y, x_off, y_off, duration=duration)
        self.__center = None

    @property
    def is_visible(self):
        return self.wait_displayed()

    @property
    def center(self):
        match = self.__center or self.wait_displayed()
        if not match:
            raise UIElementNotFoundOnScreen(self.path)
        return Point(match.x + self.width / 2, match.y + self.height / 2)

    def wait_displayed(self, timeout=5, region: Optional[Region] = None) -> Union[None, Point]:
        match = wait_condition(lambda: self.find_pattern(self.image, self.similarity, region), timeout=timeout)
        if match:
            self.__center = match
            return match

    def wait_vanish(self, timeout=30, region: Optional[Region] = None) -> bool:
        return wait_condition(lambda: self.find_pattern(self.image, self.similarity, region) is None, timeout=timeout)

    def load_image(self) -> None:
        if not Path(self.path).exists():
            raise FileNotFoundError(f'Cannot find request screenshot: {self.path}')
        image = cv2.imread(self.path, 0)
        if image is None:
            raise IOError(f'Cannot not load screenshot: {self.path}')
        height, width = image.shape
        if monitor.is_retina:
            height, width = height / 2, width / 2
        self.image, self.width, self.height = image, width, height

    @staticmethod
    def find_pattern(screenshot_path: str, min_threshold: float, region: Optional[Region] = None) -> Optional[Point]:
        """ Locate pattern on the screen and return its center.

            OpenCV (Open Source Computer Vision Library) is an open source computer vision
            and machine learning software library. It's built to provide a common infrastructure
            for computer vision applications and to accelerate the use of machine perception
            in the commercial products. """
        r = Region(0, 0, monitor.size.width, monitor.size.height) if region is None else region
        desktop = cv2.cvtColor(monitor.take_screenshot(), cv2.COLOR_BGR2GRAY)[r.y1:r.y2, r.x1:r.x2]
        _, similarity, _, position = cv2.minMaxLoc(cv2.matchTemplate(desktop, screenshot_path, cv2.TM_CCOEFF_NORMED))
        if similarity > min_threshold:
            denominator = 2 if monitor.is_retina else 1
            return Point((position[0] + r.x1) // denominator, (position[1] + r.y1) // denominator)
