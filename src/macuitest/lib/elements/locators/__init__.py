"""Declare an app's elements in one place with `Screen` classes."""

from macuitest.lib.elements.locators.accessibility import standard_window_frame
from macuitest.lib.elements.locators.factories import AppleScriptLocator
from macuitest.lib.elements.locators.factories import AXLocator
from macuitest.lib.elements.locators.factories import ImageLocator
from macuitest.lib.elements.locators.factories import TextLocator
from macuitest.lib.elements.locators.factories import applescript
from macuitest.lib.elements.locators.factories import ax
from macuitest.lib.elements.locators.factories import image
from macuitest.lib.elements.locators.factories import text
from macuitest.lib.elements.locators.factories import window
from macuitest.lib.elements.locators.screen import Screen

__all__ = [
    "AXLocator",
    "AppleScriptLocator",
    "ImageLocator",
    "Screen",
    "TextLocator",
    "applescript",
    "ax",
    "image",
    "standard_window_frame",
    "text",
    "window",
]
