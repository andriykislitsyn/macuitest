import fnmatch
from dataclasses import dataclass
from typing import List

import AppKit
from ApplicationServices import (AXIsProcessTrusted, AXUIElementCreateApplication, AXUIElementCreateSystemWide, CFEqual)
from PyObjCTools import AppHelper

from macuitest.lib.elements.native.callbacks import (get_element_action_names, get_element_attribute_names,
                                                     get_accessibility_element_attribute, get_accessibility_object_pid,
                                                     check_attribute_settable, perform_action_on_element,
                                                     set_attribute_value, set_accessibility_api_timeout,
                                                     get_accessibility_object_on_screen_position, )
from macuitest.lib.elements.native.converter import Converter
from macuitest.lib.elements.native.errors import (AXError, AXErrorAPIDisabled, AXErrorCannotComplete,
                                                  AXErrorIllegalArgument, AXErrorNotImplemented, AXErrorNoValue,
                                                  AXErrorUnsupported, )
from macuitest.lib.elements.native.element_lookup import LookUpMixin


@dataclass
class NSApplicationActivationOptions:
    Default: int = 1
    ActivateAllWindows: int = 2
    ActivateIgnoringOtherWindows: int = 3


def is_accessibility_enabled():
    """Return the status of accessibility on the system."""
    return AXIsProcessTrusted()


def get_frontmost_pid():
    """Return the process ID of the application in the foreground"""
    return AppKit.NSWorkspace.sharedWorkspace().frontmostApplication().processIdentifier()


def get_running_apps():
    """Get a list of the running applications"""
    AppHelper.callLater(1, AppHelper.stopEventLoop)
    AppHelper.runConsoleEventLoop()
    work_space = AppKit.NSWorkspace.sharedWorkspace()
    return work_space.runningApplications()


def launch_app_by_bundle_id(bundle_id: str):
    work_space = AppKit.NSWorkspace.sharedWorkspace()
    response = work_space.launchAppWithBundleIdentifier_options_additionalEventParamDescriptor_launchIdentifier_(
        bundle_id,
        AppKit.NSWorkspaceLaunchAllowingClassicStartup,
        AppKit.NSAppleEventDescriptor.nullDescriptor(),
        None,
    )
    if not response[0]:
        raise RuntimeError(f'Error launching specified application. {response}')


def launch_app_by_bundle_path(bundle_path: str, arguments=None):
    if arguments is None:
        arguments = []
    bundle_url = AppKit.NSURL.fileURLWithPath_(bundle_path)
    workspace = AppKit.NSWorkspace.sharedWorkspace()
    configuration = {AppKit.NSWorkspaceLaunchConfigurationArguments: arguments}
    return workspace.launchApplicationAtURL_options_configuration_error_(
        bundle_url,
        AppKit.NSWorkspaceLaunchAllowingClassicStartup,
        configuration, None
    )


def terminate_app_by_bundle_id(bundle_id: str):
    apps = _running_apps_with_bundle_id(bundle_id)
    if apps:
        apps[0].terminate()


def _running_apps_with_bundle_id(bundle_id: str):
    """Return an array of NSRunningApplications."""
    return AppKit.NSRunningApplication.runningApplicationsWithBundleIdentifier_(bundle_id)


class AXUIElement:
    def __init__(self, ref=None):
        self.ref = ref
        self.converter = Converter(self.__class__)

    def __repr__(self):
        _class_ = self.__class__.__name__
        for identifier in ('AXTitle', 'AXValue', 'AXRoleDescription'):
            title = getattr(self, identifier, None)
            if title:
                break
        return f'<{_class_} {getattr(self, "AXRole", "<No role!>")} "{title}">'

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return False
        if self.ref is None and other.ref is None:
            return True
        if self.ref is None or other.ref is None:
            return False
        return CFEqual(self.ref, other.ref)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __getattr__(self, item):
        if item in self.ax_attributes:
            return self._get_ax_attribute(item)
        elif item in self.ax_actions:
            def perform_ax_action():
                self._perform_ax_action(item)

            return perform_ax_action
        else:
            raise AttributeError(f'Specified object has no attribute: "{item}"')

    def __setattr__(self, key, value):
        if key.startswith('AX'):
            try:
                if key in self.ax_attributes:
                    self._set_ax_attribute(key, value)
            except AXErrorIllegalArgument:
                pass
        else:
            super(AXUIElement, self).__setattr__(key, value)

    def __dir__(self):
        return self.ax_attributes + self.ax_actions + list(self.__dict__.keys()) + dir(super(AXUIElement, self))

    @classmethod
    def from_bundle_id(cls, bundle_id):
        """Get application by the specified bundle ID."""
        matches = _running_apps_with_bundle_id(bundle_id)
        if not matches:
            raise ValueError(f'"{bundle_id}" not found among running apps.')
        return cls.from_pid(matches[0].processIdentifier())

    @classmethod
    def from_localized_name(cls, name):
        """Get the application by the specified localized name. Wildcards are also allowed."""
        for app in get_running_apps():
            if fnmatch.fnmatch(app.localizedName(), name):
                pid = app.processIdentifier()
                return cls.from_pid(pid)
        raise ValueError(f'"{name}" not found among running applications.')

    @classmethod
    def from_frontmost(cls):
        """Create an instance with the AXUIElementRef for the frontmost application."""
        for app in get_running_apps():
            pid = app.processIdentifier()
            ref = cls.from_pid(pid)
            try:
                if ref.AXFrontmost:
                    return ref
            except (AttributeError, AXErrorUnsupported, AXErrorCannotComplete, AXErrorNotImplemented):
                # Some applications do not have an explicit GUI and so will not have an AXFrontmost attribute.
                pass
        raise ValueError('No GUI applications found.')

    @classmethod
    def from_any_app_with_window(cls):
        """Create an instance with the AXUIElementRef for a random application that has windows."""
        for app in get_running_apps():
            pid = app.processIdentifier()
            ref = cls.from_pid(pid)
            if hasattr(ref, 'windows') and len(ref.windows()) > 0:
                return ref
        raise ValueError('No GUI applications found.')

    @classmethod
    def from_pid(cls, pid: int):
        """Get application by the specified process ID."""
        return cls(ref=AXUIElementCreateApplication(pid))

    @classmethod
    def systemwide(cls):
        """Create an instance with the AXUIElementRef for the system-wide accessibility object."""
        return cls(ref=AXUIElementCreateSystemWide())

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
    def bundle_id(self) -> str:
        """Get the AXUIElement's bundle identifier"""
        return self._running_app.bundleIdentifier()

    @property
    def pid(self) -> int:
        """Get the AXUIElement's process ID"""
        return get_accessibility_object_pid(self.ref)

    @property
    def _running_app(self):
        running_application = AppKit.NSRunningApplication
        return running_application.runningApplicationWithProcessIdentifier_(self.pid)

    def set_timeout(self, timeout: int) -> None:
        """Set the timeout value used in the accessibility API."""
        set_accessibility_api_timeout(self.ref, timeout)

    def activate(self) -> bool:
        """Activate the application."""
        return self._running_app.activateWithOptions_(NSApplicationActivationOptions.ActivateIgnoringOtherWindows)

    def _get_ax_attribute(self, item: str):
        """Get the value of the the specified attribute."""
        if item in self.ax_attributes:
            try:
                attribute_value = get_accessibility_element_attribute(self.ref, item)
                return self.converter.convert_value(attribute_value)
            except AXErrorNoValue:
                if item == 'AXChildren':
                    return []
                return None

        raise AttributeError(f'"{type(self)}" object has no attribute "{item}"')

    def _set_ax_attribute(self, name, value):
        """Set the specified attribute to the specified value."""
        is_settable = check_attribute_settable(self.ref, name)
        if not is_settable:
            raise AXErrorUnsupported('Attribute is not settable')
        set_attribute_value(self.ref, name, value)

    def _perform_ax_action(self, name):
        """Perform specified action on the element."""
        perform_action_on_element(self.ref, name)


class NativeUIElement(AXUIElement, LookUpMixin):
    """Expose the accessibility API in the simplest, most natural way possible."""

    def __init__(self, ref=None):
        super(NativeUIElement, self).__init__(ref=ref)
        self.__application = None

    def set_string(self, attribute, string: str):
        """Set the specified attribute to the specified string."""
        return self.__setattr__(attribute, string)

    def get_element_at_position(self, x: int, y: int):
        """Return the AXUIElement at the given coordinates."""
        if self.ref is None:
            raise AXErrorUnsupported('Operation not supported on null element references')
        element = get_accessibility_object_on_screen_position(self.ref, x, y)
        return self.__class__(element)

    def get_menu_item(self, *args):
        """ Return the specified menu item.
            Example - refer to items by name:
                app.get_menu_item('File', 'New').Press()
                app.get_menu_item('Edit', 'Insert', 'Line Break').Press()
            Refer to items by index:
                app.get_menu_item(1, 0).Press()
            Refer to items by mix-n-match:
                app.get_menu_item(1, 'About TextEdit').Press()
        """
        return self.menu_items(self.application.AXMenuBar, *args)

    @property
    def localized_name(self):
        """Return the localized name of the application."""
        return self.application.AXTitle

    @property
    def application(self):
        """Get the base application UIElement.
                If the UIElement is a child of the application, it will try
                to get the AXParent until it reaches the top application level element.
        """
        if self.__application:
            return self.__application
        app = self
        while 'AXParent' in app.ax_attributes:
            app = app.AXParent
        self.__application = app
        return self.__application
