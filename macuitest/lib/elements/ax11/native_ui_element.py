from collections import deque

from macuitest.lib.elements.ax11 import accessibility
from macuitest.lib.elements.ax11 import SearchMethodsMixin
from macuitest.lib.elements.ax11 import WaitForMixin


class NativeUIElement(WaitForMixin, SearchMethodsMixin, accessibility.AXUIElement):
    """NativeUIElement class - expose the accessibility API in the simplest, most natural way possible."""

    def __init__(self, ref=None):
        super(NativeUIElement, self).__init__(ref=ref)
        self.eventList = deque()

    @classmethod
    def get_running_apps(cls):
        """Get a list of the running applications."""
        return accessibility.get_running_apps()

    @classmethod
    def get_app_ref_by_pid(cls, pid: int):
        """Get the top level element for the application specified by pid."""
        return cls.from_pid(pid)

    @classmethod
    def get_app_ref_by_bundle_id(cls, bundle_id: str):
        """Get the top level element for the application with the specified bundle ID."""
        return cls.from_bundle_id(bundle_id)

    @classmethod
    def get_app_ref_by_localized_name(cls, name: str):
        """ Get the top level element for the application with the specified localized name.
            Wildcards are also allowed. """
        return cls.from_localized_name(name)

    @classmethod
    def get_frontmost_app(cls):
        """Get the current frontmost application."""
        return cls.frontmost()

    @classmethod
    def get_any_app_with_window(cls):
        """Get a random app that has windows."""
        return cls.with_window()

    @classmethod
    def get_system_object(cls):
        """Get the top level system accessibility object."""
        return cls.systemwide()

    @classmethod
    def set_systemwide_timeout(cls, timeout: float = 0.0):
        """Set the system-wide accessibility timeout."""
        return cls.set_systemwide_timeout(timeout)

    @staticmethod
    def launch_app_by_bundle_id(bundle_id: str):
        """Launch the application with the specified bundle ID"""
        accessibility.launch_app_by_bundle_id(bundle_id)

    @staticmethod
    def launch_app_by_bundle_path(bundle_path, arguments=None):
        """Launch app with a given bundle path."""
        return accessibility.launch_app_by_bundle_path(bundle_path, arguments)

    @staticmethod
    def terminate_app_by_bundle_id(bundle_id):
        """Terminate app with a given bundle ID."""
        return accessibility.terminate_app_by_bundle_id(bundle_id)

    def get_attributes(self):
        """Get a list of the attributes available on the element."""
        return self.ax_attributes

    def get_actions(self):
        """Return a list of the actions available on the element."""
        actions = self.ax_actions
        # strip leading AX from actions - help distinguish them from attributes
        return [action[2:] for action in actions]

    def set_string(self, attribute, string):
        """Set the specified attribute to the specified string."""
        return self.__setattr__(attribute, str(string))

    def get_element_at_position(self, coord):
        """Return the AXUIElement at the given coordinates."""
        if self.ref is None:
            raise AXErrorUnsupported("Operation not supported on null element references")
        element = PAXUIElementCopyElementAtPosition(self.ref, float(coord[0]), float(coord[1]))
        return self.__class__(element)

    def activate(self):
        """Activate the application (bringing menus and windows forward)"""
        return self._activate()

    def get_application(self):
        """Get the base application UIElement.

        If the UIElement is a child of the application, it will try
        to get the AXParent until it reaches the top application level
        element.
        """
        app = self
        while "AXParent" in app.ax_attributes:
            app = app.AXParent
        return app

    def menu_items(self, *args):
        """Return the specified menu item.

        Example - refer to items by name:

        app.menuItem('File', 'New').Press()
        app.menuItem('Edit', 'Insert', 'Line Break').Press()

        Refer to items by index:

        app.menuitem(1, 0).Press()

        Refer to items by mix-n-match:

        app.menuitem(1, 'About TextEdit').Press()
        """
        menuitem = self.get_application().AXMenuBar
        return self._menuItem(menuitem, *args)

    @property
    def bundle_id(self):
        """Return the bundle ID of the application."""
        return self.bundle_id

    @property
    def localized_name(self):
        """Return the localized name of the application."""
        return self.get_application().AXTitle

    def __getattr__(self, name):
        """Handle attribute requests in several ways:

        1. If it starts with AX, it is probably an a11y attribute. Pass
           it to the handler in _a11y which will determine that for sure.
        2. See if the attribute is an action which can be invoked on the
           UIElement. If so, return a function that will invoke the attribute.
        """
        if "AX" + name in self.ax_actions:
            action = super(NativeUIElement, self).__getattr__("AX" + name)

            def perform_specified_action():
                # activate the app before performing the specified action
                self._activate()
                return action()

            return perform_specified_action
        else:
            return super(NativeUIElement, self).__getattr__(name)
