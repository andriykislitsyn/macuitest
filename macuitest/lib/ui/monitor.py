from typing import Optional

import numpy
from Quartz import CoreGraphics as cg, CGDisplayBounds, CGMainDisplayID

from macuitest.config.constants import ScreenSize


class Monitor:
    def __init__(self):
        self.__is_retina: Optional[bool] = None
        self.__screen_size: Optional[ScreenSize] = None

    @property
    def screenshot(self) -> numpy.ndarray:
        image = cg.CGWindowListCreateImage(cg.CGRectInfinite, cg.kCGWindowListOptionOnScreenOnly,
                                           cg.kCGNullWindowID, cg.kCGWindowImageDefault)
        bytes_per_row = cg.CGImageGetBytesPerRow(image) // 4
        image = numpy.frombuffer(cg.CGDataProviderCopyData(cg.CGImageGetDataProvider(image)), dtype=numpy.uint8)
        return image.reshape((self.size.height, bytes_per_row, 4))[:, :self.size.width, :]

    @property
    def bytes(self):
        image = cg.CGWindowListCreateImage(cg.CGRectInfinite, cg.kCGWindowListOptionOnScreenOnly,
                                           cg.kCGNullWindowID, cg.kCGWindowImageDefault)
        return bytes(numpy.frombuffer(cg.CGDataProviderCopyData(cg.CGImageGetDataProvider(image)), dtype=numpy.uint8))

    @property
    def is_retina(self) -> bool:
        if self.__is_retina is None:
            self.__is_retina = self.size.width > 2000
        return self.__is_retina

    @property
    def size(self) -> ScreenSize:
        if self.__screen_size is None:
            size = CGDisplayBounds(CGMainDisplayID()).size
            self.__screen_size = ScreenSize(int(size.width), int(size.height))
        return self.__screen_size


monitor = Monitor()
