import threading
from pathlib import Path
from typing import Union, Optional

import cv2

from macuitest.config.constants import Point, Region
from macuitest.lib.core import wait_condition
from macuitest.lib.elements.controllers.mouse import mouse
from macuitest.lib.elements.ui.monitor import monitor

MATCHING_ALGORITHMS = (cv2.TM_CCOEFF_NORMED, cv2.TM_SQDIFF_NORMED)


class UIElementNotFoundOnScreen(Exception):
    """Thrown when a pattern is not found on the screen."""
    pass


class UIElement:
    """Represent a visible user interface element. Based on automated pattern lookup algorithm (OpenCV)."""

    def __init__(self, screenshot_path: Union[str, Path], similarity: float = .925):
        self.path = screenshot_path.strip() if isinstance(screenshot_path, str) else screenshot_path
        self.similarity = round(similarity, 3)
        self.image, self.width, self.height = None, None, None
        self.__center: Optional[Point] = None
        self.__matches: Optional = list()
        self.__load_image()

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

    def wait_displayed(self, timeout: int = 5, region: Optional[Region] = None) -> Union[None, Point]:
        if match := wait_condition(lambda: self.find_pattern(region), timeout=timeout):
            self.__center = match
            return match

    def wait_vanish(self, timeout: int = 15, region: Optional[Region] = None) -> bool:
        return wait_condition(
            lambda: self.find_pattern(region, algorithms=(cv2.TM_CCOEFF_NORMED,)) is None, timeout=timeout
        )

    def find_pattern(self, region: Optional[Region] = None, algorithms=MATCHING_ALGORITHMS):
        """Locate pattern on the screen and return its center.
             OpenCV (Open Source Computer Vision Library) is an open source computer vision
             and machine learning software library. It's built to provide a common infrastructure
             for computer vision applications and to accelerate the use of machine perception
             in the commercial products."""
        threads = list()
        region = region or Region(0, 0, monitor.size.width, monitor.size.height)
        desktop = cv2.cvtColor(monitor.make_snapshot(region), cv2.COLOR_BGR2GRAY)
        for algorithm in algorithms:
            x = threading.Thread(target=self.compare_by, args=(desktop, algorithm), daemon=True)
            threads.append(x)
            x.start()
        for thread in threads:
            thread.join()
        similarity, position = max(self.__matches)
        self.__matches = list()
        if similarity > self.similarity:
            denominator = 2 if monitor.is_retina else 1
            return Point((position[0] + region.x1) // denominator, (position[1] + region.y1) // denominator)

    def compare_by(self, desktop, algorithm=cv2.TM_SQDIFF_NORMED):
        min_val, max_val, min_pos, max_pos = cv2.minMaxLoc(cv2.matchTemplate(desktop, self.image, algorithm))
        (similarity, position) = round(max_val, 5), max_pos
        if algorithm == cv2.TM_SQDIFF_NORMED:
            similarity, position = round(1 - min_val, 5), min_pos
        self.__matches.append((similarity, position))
        return similarity, position

    def __load_image(self) -> None:
        """Load the image from the disk."""
        if not Path(self.path).exists():
            raise FileNotFoundError(f'Cannot find request screenshot: {self.path}')
        if (image := cv2.imread(self.path, cv2.IMREAD_GRAYSCALE)) is None:
            raise IOError(f'Cannot not load screenshot: {self.path}')
        height, width = image.shape
        if monitor.is_retina:
            height, width = height / 2, width / 2
        self.image, self.width, self.height = image, width, height
