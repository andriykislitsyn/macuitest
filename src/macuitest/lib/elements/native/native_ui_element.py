from dataclasses import dataclass
from typing import List

import AppKit
from ApplicationServices import AXUIElementCreateApplication
from ApplicationServices import AXUIElementCreateSystemWide

from macuitest.lib.elements.native.calls import AXError
from macuitest.lib.elements.native.calls import AXErrorAttributeUnsupported
from macuitest.lib.elements.native.calls import AXErrorNoValue
from macuitest.lib.elements.native.calls import AXErrorUnsupported
from macuitest.lib.elements.native.calls import check_attribute_settable
from macuitest.lib.elements.native.calls import get_accessibility_element_attribute
from macuitest.lib.elements.native.calls import get_accessibility_object_on_screen_position
from macuitest.lib.elements.native.calls import get_accessibility_object_pid
from macuitest.lib.elements.native.calls import get_element_action_names
from macuitest.lib.elements.native.calls import get_element_attribute_names
from macuitest.lib.elements.native.calls import get_running_apps
from macuitest.lib.elements.native.calls import get_running_apps_with_bundle_id
from macuitest.lib.elements.native.calls import perform_action_on_element
from macuitest.lib.elements.native.calls import set_accessibility_api_timeout
from macuitest.lib.elements.native.calls import set_attribute_value
from macuitest.lib.elements.native.converter import Converter


@dataclass
class NSApplicationActivationOptions:
    Default: int = 1
    ActivateAllWindows: int = 2
    ActivateIgnoringOtherWindows: int = 3


class NativeUIElement:
    def __init__(self, ref=None):
        self.ref = ref
        self.converter = Converter(self.__class__)
        self.__application = None

    def __repr__(self):
        for identifier in ("AXTitle", "AXValue", "AXRoleDescription"):
            title = self.get_ax_attribute(identifier)
            if title:
                title = f'"{title}"'
                break
        return f'NativeUIElement {self.get_ax_attribute("AXRole")} {title}'.strip()

    def __dir__(self):
        return self.ax_attributes + self.ax_actions + list(self.__dict__.keys()) + dir(super())

    @classmethod
    def from_bundle_id(cls, bundle_id: str):
        """Get application by the specified bundle ID."""
        matches = get_running_apps_with_bundle_id(bundle_id)
        if not matches:
            raise ValueError(f'"{bundle_id}" not found among running apps.')
        return cls.from_pid(matches[0].processIdentifier())

    @classmethod
    def from_localized_name(cls, name: str):
        """Get the application by the specified localized name. Wildcards are also allowed."""
        for app in get_running_apps():
            if app.localizedName() == name:
                return cls.from_pid(app.processIdentifier())
        raise ValueError(f'"{name}" not found among running applications.')

    @classmethod
    def from_pid(cls, pid: int):
        """Get application by the specified process ID."""
        return cls(ref=AXUIElementCreateApplication(pid))

    @classmethod
    def systemwide(cls):
        """Create an instance with the AXUIElementRef for the system-wide accessibility object."""
        return cls(ref=AXUIElementCreateSystemWide())

    def get_menu_item(self, menu: str, menu_item: str):
        """Return the specified menu item."""
        for item in self.get_menu_items(menu):
            if item.get_ax_attribute("AXTitle") == menu_item:
                return item
        raise LookupError(f'Could not find "{menu_item}" menu item')

    def get_menu_items(self, menu_name: str):
        """Return the specified menu."""
        for menu in self.get_menu_bar().get_ax_attribute("AXChildren"):
            if menu.get_ax_attribute("AXTitle") == menu_name:
                return menu.get_ax_attribute("AXChildren")[0].get_ax_attribute("AXChildren")
        raise LookupError(f'Could not find "{menu_name}" menu')

    def get_menu_bar(self):
        """Return app's menu bar."""
        for item in self.application.get_ax_attribute("AXChildren"):
            if item.get_ax_attribute("AXRole") == "AXMenuBar":
                return item
        raise LookupError("Could not find menu bar")

    def activate(self) -> bool:
        """Activate the application."""
        return self._running_app.activateWithOptions_(
            NSApplicationActivationOptions.ActivateIgnoringOtherWindows
        )

    def get_ax_attribute(self, attribute_name: str):
        """Get the value of the the specified attribute."""
        try:
            return self.converter.convert_value(
                get_accessibility_element_attribute(self.ref, attribute_name)
            )
        except (AXErrorNoValue, AXErrorAttributeUnsupported):
            return [] if attribute_name == "AXChildren" else None

    def set_ax_attribute(self, name, value):
        """Set the specified attribute to the specified value."""
        if not check_attribute_settable(self.ref, name):
            raise AXErrorUnsupported(f'Attribute "{name}" is not settable')
        set_attribute_value(self.ref, name, value)

    def press(self):
        self.perform_ax_action("AXPress")

    def perform_ax_action(self, name):
        """Perform specified action on the element."""
        perform_action_on_element(self.ref, name)

    @property
    def ax_actions(self) -> List[str]:
        """Get the list of actions available on the AXUIElement."""
        try:
            return list(get_element_action_names(self.ref))
        except AXError:
            return []

    @property
    def ax_attributes(self) -> List[str]:
        """Get the list of attributes available on the AXUIElement."""
        try:
            return list(get_element_attribute_names(self.ref))
        except AXError:
            return []

    @property
    def localized_name(self):
        """Return the localized name of the application."""
        return self.application.get_ax_attribute("AXTitle")

    @property
    def application(self):
        """Get the application accessibility object."""
        if self.__application is None:
            if self.get_ax_attribute("AXRole") == "AXApplication":
                self.__application = self
            else:
                self.__application = self.get_ax_attribute("AXTopLevelUIElement").get_ax_attribute(
                    "AXParent"
                )
        return self.__application

    def get_element_at_position(self, x: int, y: int):
        """Return the AXUIElement at the given coordinates."""
        if self.ref is None:
            raise AXErrorUnsupported("Operation not supported on null element references")
        element = get_accessibility_object_on_screen_position(self.ref, x, y)
        return self.__class__(element)

    @property
    def bundle_id(self) -> str:
        """Get the AXUIElement's bundle identifier"""
        return self._running_app.bundleIdentifier()

    @property
    def _running_app(self):
        # noinspection PyUnresolvedReferences
        return AppKit.NSRunningApplication.runningApplicationWithProcessIdentifier_(self.pid)

    @property
    def pid(self) -> int:
        """Get the AXUIElement's process ID"""
        return get_accessibility_object_pid(self.ref)

    def set_timeout(self, timeout: int) -> None:
        """Set the timeout value used in the accessibility API."""
        set_accessibility_api_timeout(self.ref, timeout)

    @property
    def focused_window(self):
        """Return the focused application window."""
        return self.application.get_ax_attribute("AXFocusedWindow")

    @property
    def windows(self):
        """Return application windows."""
        return self.application.get_ax_attribute("AXWindows")

    @property
    def children(self) -> list:
        return self.get_ax_attribute("AXChildren")

    def find_element(self, recursive: bool = False, **kwargs):
        """Return the first object that matches lookup criteria."""
        for item in self.get_children(recursive=recursive):
            if match_filter(**kwargs)(item):
                return item

    def find_elements(self, recursive: bool = False, **kwargs):
        """Return a list of all child elements that match lookup criteria."""
        return list(filter(match_filter(**kwargs), self.get_children(recursive=recursive)))

    def get_children(self, target=None, recursive: bool = False):
        """Generator yielding child objects."""
        if target is None:
            target = self
        for child in target.get_ax_attribute("AXChildren"):
            yield child
            if recursive:
                for c in self.get_children(child, recursive):
                    yield c


def match_filter(**attributes):
    def _match(ax_object):
        for attribute in attributes.keys():
            try:
                value = ax_object.get_ax_attribute(attribute)
                if value != attributes.get(attribute):
                    return False
            except AttributeError:
                return False
        return True

    return _match
