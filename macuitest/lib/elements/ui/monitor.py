from typing import Optional

import numpy
import AppKit
from Quartz import CoreGraphics, CGDisplayBounds, CGMainDisplayID

from macuitest.config.constants import ScreenSize


class Monitor:
    def __init__(self):
        self.__is_retina: Optional[bool] = None
        self.__screen_size: Optional[ScreenSize] = None

    def take_screenshot(self) -> numpy.ndarray:
        pixel_data = self.pixel_data
        _image = numpy.frombuffer(pixel_data[0], dtype=numpy.uint8)
        return _image.reshape((self.size.height, pixel_data[1], 4))[:, :self.size.width, :]

    @property
    def bytes(self):
        return bytes(numpy.frombuffer(self.pixel_data[0], numpy.uint8))

    @property
    def is_retina(self) -> bool:
        if self.__is_retina is None:
            self.__is_retina = AppKit.NSScreen.mainScreen().backingScaleFactor() > 1.0
        return self.__is_retina

    @property
    def size(self) -> ScreenSize:
        if self.__screen_size is None:
            size = CGDisplayBounds(CGMainDisplayID()).size
            self.__screen_size = ScreenSize(int(size.width), int(size.height))
        return self.__screen_size

    @property
    def pixel_data(self):
        image = CoreGraphics.CGWindowListCreateImage(
            CoreGraphics.CGRectInfinite,
            CoreGraphics.kCGWindowListOptionOnScreenOnly,
            CoreGraphics.kCGNullWindowID,
            CoreGraphics.kCGWindowImageDefault
        )
        pixel_data = CoreGraphics.CGDataProviderCopyData(CoreGraphics.CGImageGetDataProvider(image))
        bytes_per_row = CoreGraphics.CGImageGetBytesPerRow(image) // 4
        return pixel_data, bytes_per_row


monitor = Monitor()
print(monitor.is_retina)