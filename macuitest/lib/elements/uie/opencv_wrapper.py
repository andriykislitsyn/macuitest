"""OpenCV (Open Source Computer Vision Library) wrapper.
OpenCV (Open Source Computer Vision Library) is an open source computer vision and machine learning software library.
OpenCV was built to provide a common infrastructure for computer vision applications and to accelerate the use
of machine perception in the commercial products. Being a BSD-licensed product, OpenCV makes it easy for businesses
to utilize and modify the code."""
from typing import Tuple, Optional

import cv2
import mss
import numpy
from Quartz import CGDisplayBounds, CGMainDisplayID

from macuitest.config.constants import Point, Region, ScreenSize


class _WrapperOpenCV:
    def __init__(self):
        self._is_retina: Optional[bool] = None
        self._screen_size: Optional[Tuple[int, int]] = None

    def find_pattern(self, pattern, sim: float, region: Region) -> Optional[Point]:
        """Locate pattern on the screen and return its center."""
        _result = cv2.matchTemplate(
            self.screenshot[region.y1:region.y2, region.x1:region.x2], pattern, cv2.TM_CCOEFF_NORMED
        )
        _, similarity, _, position = cv2.minMaxLoc(_result)
        if similarity > sim:
            denominator = 2 if self.is_retina_display else 1
            return Point((position[0] + region.x1) // denominator, (position[1] + region.y1) // denominator)

    @property
    def screenshot(self) -> numpy.ndarray:
        """Make a screenshot of the screen and convert to CV2 Image object."""
        _monitor = None
        with mss.mss() as sct:
            for monitor in sct.monitors:
                if monitor.get('width') <= 1920:  # We want to launch tests on non-Retina displays only.
                    _monitor = monitor
                    break
            _desktop = sct.grab(_monitor)
        return cv2.cvtColor(numpy.array(_desktop)[:, :, ::-1].copy(), cv2.COLOR_BGR2GRAY)  # Greyscale image.

    @property
    def is_retina_display(self) -> bool:
        if self._is_retina is None:
            self._is_retina = self.screen_size.width > 2000
        return self._is_retina

    @property
    def screen_size(self) -> ScreenSize:
        if self._screen_size is None:
            size = CGDisplayBounds(CGMainDisplayID()).size
            self._screen_size = ScreenSize(int(size.width), int(size.height))
        return self._screen_size


opencv_wrapper = _WrapperOpenCV()
