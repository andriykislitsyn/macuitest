from pathlib import Path
from typing import Optional
from typing import Tuple
from typing import Union

import AppKit
import numpy
import Quartz
from Foundation import NSURL
from Quartz import CGDisplayBounds
from Quartz import CGMainDisplayID
from Quartz import CoreGraphics

from macuitest.config.constants import Region
from macuitest.config.constants import ScreenSize


class Monitor:
    def __init__(self):
        self.__is_retina: Optional[bool] = None
        self.__screen_size: Optional[ScreenSize] = None

    def make_snapshot(self, region: Optional[Region] = None) -> numpy.ndarray:
        h, w = (
            (region.y2 - region.y1, region.x2 - region.x1)
            if region
            else (self.size.height, self.size.width)
        )
        pixel_data = self.get_pixel_data(region=region)
        _image = numpy.frombuffer(pixel_data[0], dtype=numpy.uint8)
        return _image.reshape((h, pixel_data[1], 4))[:, :w, :]

    @property
    def bytes(self):
        return bytes(numpy.frombuffer(self.get_pixel_data()[0], numpy.uint8))

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

    @staticmethod
    def get_pixel_data(region: Optional[Region] = None):
        region = (
            CoreGraphics.CGRectInfinite
            if region is None
            else CoreGraphics.CGRectMake(
                region.x1, region.y1, region.x2 - region.x1, region.y2 - region.y1
            )
        )
        image = CoreGraphics.CGWindowListCreateImage(
            region,
            CoreGraphics.kCGWindowListOptionOnScreenOnly,
            CoreGraphics.kCGNullWindowID,
            CoreGraphics.kCGWindowImageDefault,
        )
        pixel_data = CoreGraphics.CGDataProviderCopyData(CoreGraphics.CGImageGetDataProvider(image))
        bytes_per_row = CoreGraphics.CGImageGetBytesPerRow(image) // 4
        return pixel_data, bytes_per_row

    @staticmethod
    def save_screenshot(
        where: Union[str, Path], region: Optional[Tuple[int, int, int, int]] = None
    ) -> Union[str, Path]:
        """Take a screenshot and save it to `where.
        Note: Region is defined by (x, y) pair of top left point, and width, length params.
        """
        region = CoreGraphics.CGRectInfinite if region is None else CoreGraphics.CGRectMake(*region)
        image = CoreGraphics.CGWindowListCreateImage(
            region,
            CoreGraphics.kCGWindowListOptionOnScreenOnly,
            CoreGraphics.kCGNullWindowID,
            CoreGraphics.kCGWindowImageDefault,
        )
        destination = Quartz.CGImageDestinationCreateWithURL(
            NSURL.fileURLWithPath_(str(where)), "public.png", 1, None
        )
        Quartz.CGImageDestinationAddImage(destination, image, dict())
        Quartz.CGImageDestinationFinalize(destination)
        return where


monitor = Monitor()
