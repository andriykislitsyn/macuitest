from pathlib import Path
from typing import Optional, Union, Tuple

import AppKit
import Quartz
import numpy
from Foundation import NSURL
from Quartz import CoreGraphics, CGDisplayBounds, CGMainDisplayID

from macuitest.config.constants import ScreenSize


class Monitor:
    def __init__(self):
        self.__is_retina: Optional[bool] = None
        self.__screen_size: Optional[ScreenSize] = None

    @property
    def snapshot(self) -> numpy.ndarray:
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

    @staticmethod
    def save_screenshot(where: Union[str, Path], region: Optional[Tuple[int, int, int, int]] = None):
        region = CoreGraphics.CGRectInfinite if region is None else CoreGraphics.CGRectMake(*region)
        image = CoreGraphics.CGWindowListCreateImage(
            region,
            CoreGraphics.kCGWindowListOptionOnScreenOnly,
            CoreGraphics.kCGNullWindowID,
            CoreGraphics.kCGWindowImageDefault
        )
        destination = Quartz.CGImageDestinationCreateWithURL(NSURL.fileURLWithPath_(str(where)), 'public.png', 1, None)
        Quartz.CGImageDestinationAddImage(destination, image, dict())
        Quartz.CGImageDestinationFinalize(destination)


monitor = Monitor()
