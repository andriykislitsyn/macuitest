from pathlib import Path
from typing import Optional
from typing import Sequence
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
from macuitest.lib.operating_system.permissions import require_screen_recording

MAX_DISPLAYS = 16


def _region(rect) -> Region:
    return Region(
        x1=int(rect.origin.x),
        y1=int(rect.origin.y),
        x2=int(rect.origin.x + rect.size.width),
        y2=int(rect.origin.y + rect.size.height),
    )


class Monitor:
    def __init__(self):
        self.__is_retina: Optional[bool] = None
        self.__screen_size: Optional[ScreenSize] = None
        self.__bounds: Optional[Region] = None
        self.__displays: Optional[list[Region]] = None

    def make_snapshot(self, region: Optional[Region] = None) -> numpy.ndarray:
        pixel_data, row_stride, width, height = self.get_pixel_data(region=region)
        _image = numpy.frombuffer(pixel_data, dtype=numpy.uint8)
        return _image.reshape((height, row_stride, 4))[:, :width, :]

    @property
    def displays(self) -> list[Region]:
        """Every active display's bounds in global Quartz points, menu bar display first."""
        if self.__displays is None:
            _, display_ids, count = CGGetActiveDisplayList(MAX_DISPLAYS, None, None)
            self.__displays = [_region(CGDisplayBounds(display)) for display in display_ids[:count]]
        return self.__displays

    @property
    def bounds(self) -> Region:
        """The union bounding box of every connected display, in global Quartz points.

        Unlike `size`, which covers only the main display, this includes displays at negative
        offsets, such as a secondary monitor placed to the left of or above the main one.
        """
        if self.__bounds is None:
            displays = self.displays
            self.__bounds = Region(
                x1=min(d.x1 for d in displays),
                y1=min(d.y1 for d in displays),
                x2=max(d.x2 for d in displays),
                y2=max(d.y2 for d in displays),
            )
        return self.__bounds

    @property
    def bytes(self):
        return bytes(numpy.frombuffer(self.get_pixel_data()[0], numpy.uint8))

    @property
    def is_retina(self) -> bool:
        """Whether the menu bar display has more than one pixel per point."""
        if self.__is_retina is None:
            # screens()[0] holds the menu bar. mainScreen() follows the key window instead.
            self.__is_retina = AppKit.NSScreen.screens()[0].backingScaleFactor() > 1.0
        return self.__is_retina

    @property
    def size(self) -> ScreenSize:
        if self.__screen_size is None:
            size = CGDisplayBounds(CGMainDisplayID()).size
            self.__screen_size = ScreenSize(int(size.width), int(size.height))
        return self.__screen_size

    @staticmethod
    def capture(region: Optional[Region] = None):
        """Return a CGImage of `region`, given in global points, or of every display when None.

        Raises:
            ValueError: `region` has no width or height.
            PermissionError: Screen Recording isn't granted.
        """
        if region is not None and (region.x2 <= region.x1 or region.y2 <= region.y1):
            raise ValueError(f"Cannot capture an empty region: {region}")
        require_screen_recording()
        rect = (
            CoreGraphics.CGRectInfinite
            if region is None
            else CoreGraphics.CGRectMake(
                region.x1, region.y1, region.x2 - region.x1, region.y2 - region.y1
            )
        )
        return CoreGraphics.CGWindowListCreateImage(
            rect,
            CoreGraphics.kCGWindowListOptionOnScreenOnly,
            CoreGraphics.kCGNullWindowID,
            CoreGraphics.kCGWindowImageDefault,
        )

    @staticmethod
    def capture_window(window_number: int):
        """Return a CGImage of one window, even while other windows cover it or it's off screen.

        Raises:
            PermissionError: Screen Recording isn't granted.
        """
        require_screen_recording()
        return CoreGraphics.CGWindowListCreateImage(
            CoreGraphics.CGRectNull,
            CoreGraphics.kCGWindowListOptionIncludingWindow,
            window_number,
            CoreGraphics.kCGWindowImageBoundsIgnoreFraming,
        )

    @staticmethod
    def capture_windows(window_numbers: Sequence[int], region: Region):
        """Return a CGImage of `region` showing only the given windows, even under other windows.

        Raises:
            PermissionError: Screen Recording isn't granted.
        """
        require_screen_recording()
        rect = CoreGraphics.CGRectMake(
            region.x1, region.y1, region.x2 - region.x1, region.y2 - region.y1
        )
        return CoreGraphics.CGWindowListCreateImageFromArray(
            rect, list(window_numbers), CoreGraphics.kCGWindowImageBoundsIgnoreFraming
        )

    @staticmethod
    def get_pixel_data(region: Optional[Region] = None):
        image = Monitor.capture(region)
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
