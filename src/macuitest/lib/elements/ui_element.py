from pathlib import Path
from typing import Optional
from typing import Union

import cv2
import numpy
import Quartz
from Foundation import NSURL

from macuitest.config.constants import POINTS_PER_INCH
from macuitest.config.constants import Point
from macuitest.config.constants import Region
from macuitest.config.settings import settings
from macuitest.lib.elements.screen_element import ScreenElement
from macuitest.lib.elements.screen_element import (
    UIElementNotFoundOnScreen as UIElementNotFoundOnScreen,  # Re-exported for existing imports.
)
from macuitest.lib.elements.screen_element import default_region
from macuitest.lib.elements.ui.matching import find_template
from macuitest.lib.elements.ui.monitor import monitor


class UIElement(ScreenElement):
    """Visible user interface element. Based on automated pattern lookup algorithm (OpenCV)."""

    def __init__(self, screenshot_path: Union[str, Path], similarity: Optional[float] = None):
        self.path = screenshot_path.strip() if isinstance(screenshot_path, str) else screenshot_path
        self.__similarity = similarity
        self.image = self.__load_image()
        # A pattern without a recorded scale is assumed captured on the menu bar display.
        self.__template_scale = recorded_scale(self.path) or (2 if monitor.is_retina else 1)
        height, width = self.image.shape
        self.width, self.height = width / self.__template_scale, height / self.__template_scale
        self.__templates = {float(self.__template_scale): self.image}

    def __repr__(self):
        return f'<UIElement "{self.path}", similarity={self.similarity}>'

    def detect_on_screen(self, region: Optional[Region] = None) -> Optional[Point]:
        """Return the top-left point of the best match in `region`, or None below `similarity`.

        `region` defaults to `default_region()`, then to every connected display.

        Raises:
            ValueError: `region` is empty.
            cv2.error: `region` is narrower or shorter than the pattern.
        """
        region = region or default_region() or monitor.bounds
        screen = cv2.cvtColor(monitor.make_snapshot(region), cv2.COLOR_BGRA2GRAY)
        capture_scale = screen.shape[1] / (region.x2 - region.x1)
        match = find_template(screen, self.__template_at(capture_scale), self.similarity)
        if match is not None:
            return Point(
                region.x1 + int(match[0] / capture_scale), region.y1 + int(match[1] / capture_scale)
            )
        return None

    def _locate(self, region: Optional[Region]) -> Optional[Region]:
        match = self.detect_on_screen(region)
        if match is None:
            return None
        return Region(match.x, match.y, match.x + self.width, match.y + self.height)

    @property
    def similarity(self) -> float:
        """The minimum match score, `settings.elements.similarity` unless set on this element."""
        return settings.elements.similarity if self.__similarity is None else self.__similarity

    @similarity.setter
    def similarity(self, value: Optional[float]):
        self.__similarity = value

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

    def __load_image(self) -> numpy.ndarray:
        """Load the image from disk in grayscale."""
        if not Path(self.path).exists():
            raise FileNotFoundError(f"Cannot find request screenshot: {self.path}")
        image = cv2.imread(str(self.path), cv2.IMREAD_GRAYSCALE)
        if image is None:
            raise IOError(f"Cannot not load screenshot: {self.path}")
        return image


def recorded_scale(path: Union[str, Path]) -> Optional[int]:
    """Return the pixels per point a PNG's DPI records: 1, 2, or 3.

    Returns:
        None when the PNG records no DPI, or one that isn't 72, 144, or 216, such as an
        image editor's 300.
    """
    source = Quartz.CGImageSourceCreateWithURL(NSURL.fileURLWithPath_(str(path)), None)
    properties = source and Quartz.CGImageSourceCopyPropertiesAtIndex(source, 0, None)
    dpi = properties and properties.get(Quartz.kCGImagePropertyDPIWidth)
    if dpi is None:
        return None
    scale, remainder = divmod(dpi, POINTS_PER_INCH)
    return int(scale) if remainder == 0 and scale in (1, 2, 3) else None
