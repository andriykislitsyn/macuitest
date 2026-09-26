from pathlib import Path
from typing import Optional
from typing import Tuple
from typing import Union

import AppKit
import numpy
import Quartz
from Foundation import NSURL
from Quartz import CGDisplayBounds
from Quartz import CGGetActiveDisplayList
from Quartz import CGMainDisplayID
from Quartz import CoreGraphics

from macuitest.config.constants import Region
from macuitest.config.constants import ScreenSize

MAX_DISPLAYS = 16


class Monitor:
    def __init__(self):
        self.__is_retina: Optional[bool] = None
        self.__screen_size: Optional[ScreenSize] = None
        self.__bounds: Optional[Region] = None

    def make_snapshot(self, region: Optional[Region] = None) -> numpy.ndarray:
        pixel_data, row_stride, width, height = self.get_pixel_data(region=region)
        _image = numpy.frombuffer(pixel_data, dtype=numpy.uint8)
        return _image.reshape((height, row_stride, 4))[:, :width, :]

    @property
    def bounds(self) -> Region:
        """Return the union bounding box of every connected display, in global Quartz points.

        Unlike `size`, which covers only the main display, this includes displays at negative
        offsets, such as a secondary monitor placed to the left of or above the main one.
        """
        if self.__bounds is None:
            _, display_ids, count = CGGetActiveDisplayList(MAX_DISPLAYS, None, None)
            rects = [CGDisplayBounds(display_id) for display_id in display_ids[:count]]
            self.__bounds = Region(
                x1=int(min(r.origin.x for r in rects)),
                y1=int(min(r.origin.y for r in rects)),
                x2=int(max(r.origin.x + r.size.width for r in rects)),
                y2=int(max(r.origin.y + r.size.height for r in rects)),
            )
        return self.__bounds

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
        row_stride = CoreGraphics.CGImageGetBytesPerRow(image) // 4
        width = CoreGraphics.CGImageGetWidth(image)
        height = CoreGraphics.CGImageGetHeight(image)
        return pixel_data, row_stride, width, height

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
