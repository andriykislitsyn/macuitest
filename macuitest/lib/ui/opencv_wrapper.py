"""OpenCV (Open Source Computer Vision Library) wrapper.
OpenCV (Open Source Computer Vision Library) is an open source computer vision and machine learning software library.
OpenCV was built to provide a common infrastructure for computer vision applications and to accelerate the use
of machine perception in the commercial products. Being a BSD-licensed product, OpenCV makes it easy for businesses
to utilize and modify the code."""
from typing import Optional

import cv2

from macuitest.config.constants import Point, Region
from macuitest.lib.ui.monitor import monitor


class _WrapperOpenCV:
    algorithm = cv2.TM_CCOEFF_NORMED

    def __init__(self, display: monitor):
        self.display = display

    def find_pattern(self, pattern, sim: float, region: Optional[Region] = None) -> Optional[Point]:
        """Locate pattern on the screen and return its center."""
        region = Region(0, 0, self.display.size.width, self.display.size.height) if region is None else region
        desktop = cv2.cvtColor(self.display.screenshot, cv2.COLOR_BGR2GRAY)[region.y1:region.y2, region.x1:region.x2]
        _, similarity, _, position = cv2.minMaxLoc(cv2.matchTemplate(desktop, pattern, self.algorithm))
        if similarity > sim:
            denominator = 2 if self.display.is_retina else 1
            return Point((position[0] + region.x1) // denominator, (position[1] + region.y1) // denominator)


opencv_wrapper = _WrapperOpenCV(monitor)
