"""Declare an app's elements in one place with `Screen` classes."""

from macuitest.lib.elements.locators.factories import applescript
from macuitest.lib.elements.locators.factories import ax
from macuitest.lib.elements.locators.factories import image
from macuitest.lib.elements.locators.factories import text
from macuitest.lib.elements.locators.screen import Screen

__all__ = ["Screen", "applescript", "ax", "image", "text"]
