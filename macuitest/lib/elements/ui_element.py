import threading
from pathlib import Path
from typing import Union, Optional

import cv2

from macuitest.config.constants import Point, Region
from macuitest.lib.core import wait_condition
from macuitest.lib.elements.controllers.mouse import mouse, MouseConfig
from macuitest.lib.elements.ui.monitor import monitor

MATCHING_ALGORITHMS = (cv2.TM_CCOEFF_NORMED, cv2.TM_SQDIFF_NORMED)


class UIElementNotFoundOnScreen(Exception):
    """Thrown when a pattern is not found on the screen."""


class UIElement:
    """Visible user interface element. Based on automated pattern lookup algorithm (OpenCV)."""

    def __init__(self, screenshot_path: Union[str, Path], similarity: float = .925):
        self.path = screenshot_path.strip() if isinstance(screenshot_path, str) else screenshot_path
        self.similarity: float = round(similarity, 3)
        self.image, self.width, self.height = None, None, None
        self.__matches: Optional = list()
        self.__load_image()

    def __repr__(self):
        return f'<UIElement "{self.path}", sim={self.similarity}>'

    def paste(self, x_off: int = 0, y_off: int = 0, phrase: str = '', region: Optional[Region] = None):
        center = self.get_center(region)
        mouse.paste(center.x + x_off, center.y + y_off, phrase=phrase)

    def double_click(self, x_off: int = 0, y_off: int = 0, region: Optional[Region] = None):
        center = self.get_center(region)
        mouse.double_click(center.x + x_off, center.y + y_off)

    def right_click(self, x_off: int = 0, y_off: int = 0, hold: float = MouseConfig.hold,
                    pause: float = MouseConfig.pause, region: Optional[Region] = None):
        center = self.get_center(region)
        mouse.right_click(center.x + x_off, center.y + y_off, hold=hold, pause=pause)

    def click_mouse(self, x_off: int = 0, y_off: int = 0, hold: float = MouseConfig.hold,
                    pause: float = MouseConfig.pause, region: Optional[Region] = None):
        center = self.get_center(region)
        mouse.click(center.x + x_off, center.y + y_off, hold=hold, pause=pause)

    def hover_mouse(self, x_off: int = 0, y_off: int = 0, duration: float = MouseConfig.move,
                    region: Optional[Region] = None):
        center = self.get_center(region)
        mouse.hover(center.x + x_off, center.y + y_off, duration=duration)

    @property
    def is_visible(self) -> bool:
        """Check whether the pattern is visible on the screen."""
        return False or self.wait_displayed() is not None

    def get_center(self, region: Optional[Region] = None):
        match = self.wait_displayed(region=region)
        if not match:
            raise UIElementNotFoundOnScreen(self.path)
        return Point(int(match.x + self.width / 2), int(match.y + self.height / 2))

    def wait_displayed(self, timeout: int = 5, region: Optional[Region] = None) -> Union[None, Point]:
        return wait_condition(lambda: self.find_pattern(region), timeout=timeout)

    def wait_vanish(self, timeout: int = 15, region: Optional[Region] = None) -> bool:
        return wait_condition(lambda: self.find_pattern(region, algorithms=(cv2.TM_CCOEFF_NORMED,)) is None,
                              timeout=timeout)

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
        # In case of AssertionError in cv2.error
        # _img.size().height <= _templ.size().height && _img.size().width <= _templ.size().width
        # You need to check that the `region` size is larger than `pattern` size.
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
