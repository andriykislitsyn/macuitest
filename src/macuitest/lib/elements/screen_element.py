"""Base class for elements found by looking at the screen."""

from abc import ABC
from abc import abstractmethod
from typing import Optional

from macuitest.config.constants import Point
from macuitest.config.constants import Region
from macuitest.config.settings import settings
from macuitest.lib.core import wait_condition
from macuitest.lib.elements.controllers.mouse import mouse
from macuitest.lib.elements.ui.monitor import monitor


class UIElementNotFoundOnScreen(Exception):
    """Raised when an element isn't found on the screen."""


def default_region() -> Optional[Region]:
    """Return `settings.screen.search_region`, else the bounds of `settings.screen.display`.

    None means every display.
    """
    if settings.screen.search_region is not None:
        return settings.screen.search_region
    if settings.screen.display is not None:
        return monitor.displays[settings.screen.display]
    return None


class ScreenElement(ABC):
    """Element located by looking at the screen.

    Mouse actions wait for the element, then act at its center plus `x_off` and `y_off`. They
    raise `UIElementNotFoundOnScreen` like `get_center`.
    """

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
        """Whether the element appears on screen within `settings.elements.timeout` seconds."""
        return bool(self.wait_displayed())

    def get_center(self, region: Optional[Region] = None) -> Point:
        """Return the center of the element's box in global display points.

        Raises:
            UIElementNotFoundOnScreen: The element doesn't appear within
                `settings.elements.timeout` seconds.
        """
        box = self.wait_displayed(region=region)
        if not box:
            raise UIElementNotFoundOnScreen(repr(self))
        return Point(int((box.x1 + box.x2) / 2), int((box.y1 + box.y2) / 2))

    def wait_displayed(
        self, timeout: Optional[float] = None, region: Optional[Region] = None
    ) -> Optional[Region]:
        """Return the element's box once it appears, or None after `timeout` seconds.

        `timeout` defaults to `settings.elements.timeout`.
        """
        timeout = settings.elements.timeout if timeout is None else timeout
        return wait_condition(lambda: self.locate(region), timeout=timeout) or None

    def wait_vanish(self, timeout: Optional[float] = None, region: Optional[Region] = None) -> bool:
        """Return whether the element disappears within `timeout` seconds.

        `timeout` defaults to `settings.elements.vanish_timeout`.
        """
        timeout = settings.elements.vanish_timeout if timeout is None else timeout
        return wait_condition(lambda: self.locate(region) is None, timeout=timeout)
