from pathlib import Path
from typing import Optional
from typing import Union

import cv2
import numpy

from macuitest.config.constants import Point
from macuitest.config.constants import Region
from macuitest.lib.core import wait_condition
from macuitest.lib.elements.controllers.mouse import mouse
from macuitest.lib.elements.ui.matching import find_template
from macuitest.lib.elements.ui.monitor import monitor


class UIElementNotFoundOnScreen(Exception):
    """Thrown when a pattern is not found on the screen."""


class UIElement:
    """Visible user interface element. Based on automated pattern lookup algorithm (OpenCV)."""

    def __init__(self, screenshot_path: Union[str, Path], similarity: float = 0.925):
        self.path = screenshot_path.strip() if isinstance(screenshot_path, str) else screenshot_path
        self.similarity: float = similarity
        # Patterns are assumed captured on the menu bar display, at its pixels per point.
        self.__template_scale = 2 if monitor.is_retina else 1
        self.image, self.width, self.height = self.__load_image()
        self.__templates = {float(self.__template_scale): self.image}

    def __repr__(self):
        return f'<UIElement "{self.path}", similarity={self.similarity}>'

    def paste(
        self, x_off: int = 0, y_off: int = 0, phrase: str = "", region: Optional[Region] = None
    ):
        center = self.get_center(region)
        mouse.paste(center.x + x_off, center.y + y_off, phrase=phrase)

    def double_click(self, x_off: int = 0, y_off: int = 0, region: Optional[Region] = None):
        center = self.get_center(region)
        mouse.double_click(center.x + x_off, center.y + y_off)

    def right_click(
        self,
        x_off: int = 0,
        y_off: int = 0,
        hold: Optional[float] = None,
        pause: Optional[float] = None,
        region: Optional[Region] = None,
    ):
        center = self.get_center(region)
        mouse.right_click(center.x + x_off, center.y + y_off, hold=hold, pause=pause)

    def click_mouse(
        self,
        x_off: int = 0,
        y_off: int = 0,
        hold: Optional[float] = None,
        pause: Optional[float] = None,
        region: Optional[Region] = None,
    ):
        center = self.get_center(region)
        mouse.click(center.x + x_off, center.y + y_off, hold=hold, pause=pause)

    def hover_mouse(
        self,
        x_off: int = 0,
        y_off: int = 0,
        duration: Optional[float] = None,
        region: Optional[Region] = None,
    ):
        center = self.get_center(region)
        mouse.hover(center.x + x_off, center.y + y_off, duration=duration)

    @property
    def is_visible(self) -> bool:
        """Check whether the pattern is visible on the screen."""
        return bool(self.wait_displayed())

    def get_center(self, region: Optional[Region] = None):
        match = self.wait_displayed(region=region)
        if not match:
            raise UIElementNotFoundOnScreen(self.path)
        return Point(int(match.x + self.width / 2), int(match.y + self.height / 2))

    def wait_displayed(
        self, timeout: int = 5, region: Optional[Region] = None
    ) -> Union[None, Point]:
        return wait_condition(lambda: self.detect_on_screen(region), timeout=timeout)

    def wait_vanish(self, timeout: int = 15, region: Optional[Region] = None) -> bool:
        return wait_condition(lambda: self.detect_on_screen(region) is None, timeout=timeout)

    def detect_on_screen(self, region: Optional[Region] = None) -> Optional[Point]:
        """Return the top-left point of the best match in `region`, or None below `similarity`.

        `region` defaults to every connected display.

        Raises:
            cv2.error: `region` is narrower or shorter than the pattern.
        """
        region = region or monitor.bounds
        screen = cv2.cvtColor(monitor.make_snapshot(region), cv2.COLOR_BGRA2GRAY)
        capture_scale = screen.shape[1] / (region.x2 - region.x1)
        match = find_template(screen, self.__template_at(capture_scale), self.similarity)
        if match is not None:
            return Point(
                region.x1 + int(match[0] / capture_scale), region.y1 + int(match[1] / capture_scale)
            )
        return None

    def __template_at(self, capture_scale: float) -> numpy.ndarray:
        """Return the pattern resampled to `capture_scale` pixels per point, cached per scale."""
        capture_scale = round(capture_scale, 2)
        if capture_scale not in self.__templates:
            ratio = capture_scale / self.__template_scale
            interpolation = cv2.INTER_AREA if ratio < 1 else cv2.INTER_CUBIC
            self.__templates[capture_scale] = cv2.resize(
                self.image, None, fx=ratio, fy=ratio, interpolation=interpolation
            )
        return self.__templates[capture_scale]

    def __load_image(self) -> tuple[numpy.ndarray, float, float]:
        """Load the image from disk and return it with its width and height in points."""
        if not Path(self.path).exists():
            raise FileNotFoundError(f"Cannot find request screenshot: {self.path}")
        image = cv2.imread(str(self.path), cv2.IMREAD_GRAYSCALE)
        if image is None:
            raise IOError(f"Cannot not load screenshot: {self.path}")
        height, width = image.shape
        return image, width / self.__template_scale, height / self.__template_scale
