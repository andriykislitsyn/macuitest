"""Base class for elements found by looking at the screen."""

from abc import ABC
from abc import abstractmethod
from dataclasses import dataclass
from typing import Optional

from macuitest.config.constants import Point
from macuitest.config.constants import Region
from macuitest.lib.core import wait_condition
from macuitest.lib.elements.controllers.mouse import mouse


class UIElementNotFoundOnScreen(Exception):
    """Thrown when an element is not found on the screen."""


@dataclass
class ScreenConfig:
    """Default screen search settings.

    Elements read these whenever a `region` argument is None, so assigning one, such as
    `ScreenConfig.search_region = monitor.displays[1]`, changes every later lookup.
    """

    search_region: Optional[Region] = None  # None searches every display.


class ScreenElement(ABC):
    """Element located by looking at the screen, with mouse actions at its center."""

    @abstractmethod
    def locate(self, region: Optional[Region] = None) -> Optional[Region]:
        """Return the element's box in global display points, or None if it isn't on screen."""

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
        """Check whether the element is visible on the screen."""
        return bool(self.wait_displayed())

    def get_center(self, region: Optional[Region] = None) -> Point:
        """Return the center of the element's box in global display points.

        Raises:
            UIElementNotFoundOnScreen: The element doesn't appear within the default timeout.
        """
        box = self.wait_displayed(region=region)
        if not box:
            raise UIElementNotFoundOnScreen(repr(self))
        return Point(int((box.x1 + box.x2) / 2), int((box.y1 + box.y2) / 2))

    def wait_displayed(self, timeout: int = 5, region: Optional[Region] = None) -> Optional[Region]:
        """Return the element's box once it appears, or None after `timeout` seconds."""
        return wait_condition(lambda: self.locate(region), timeout=timeout) or None

    def wait_vanish(self, timeout: int = 15, region: Optional[Region] = None) -> bool:
        """Return whether the element disappears within `timeout` seconds."""
        return wait_condition(lambda: self.locate(region) is None, timeout=timeout)
