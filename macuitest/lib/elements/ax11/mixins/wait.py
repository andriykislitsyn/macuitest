from macuitest.lib.elements.ax11 import match_filter
from macuitest.lib.elements.ax11 import Observer


class WaitForMixin:
    def wait_for_creation(self, timeout=10, notification="AXCreated"):
        """Convenience method to wait for creation of some UI element."""
        return self.wait_for(timeout, notification)

    def wait_for_window_to_appear(self, window_name, timeout=10):
        return self.wait_for(timeout, "AXWindowCreated", AXTitle=window_name)

    def wait_for_window_to_disappear(self, window_name, timeout=10):
        _ = self.findFirst(AXRole="AXWindow", AXTitle=window_name)
        return self.wait_for(timeout, "AXUIElementDestroyed", AXRole="AXWindow", AXTitle=window_name)

    def wait_for_sheet_to_appear(self, timeout=10):
        return self.wait_for_creation(timeout, "AXSheetCreated")

    def wait_for_value_to_change(self, timeout=10):
        """Wait for value attribute of given element to change.
            Some types of elements (e.g. menu items) have their titles change,
            so this will not work for those. This seems to work best if you set
            the notification at the application level.
        """
        # Want to identify that the element whose value changes matches this
        # object's.  Unique identifiers considered include role and position
        # This seems to work best if you set the notification at the application level
        return self.wait_for(timeout, "AXValueChanged")

    def wait_for_focus_to_change(self, new_focused_element, timeout=10):
        return self.wait_for(
            timeout,
            "AXFocusedUIElementChanged",
            AXRole=new_focused_element.AXRole,
            AXPosition=new_focused_element.AXPosition,
        )

    def wait_for_focused_window_to_change(self, next_window_name, timeout=10):
        return self.wait_for(timeout, "AXFocusedWindowChanged", AXTitle=next_window_name)

    def wait_for_focus_to_match_criteria(self, timeout=10, **kwargs):
        """Wait for focused element to change (to element matching kwargs criteria)."""
        return self.wait_for(timeout, "AXFocusedUIElementChanged", **kwargs)

    def wait_for(self, timeout, notification, **kwargs):
        """Generic wait for a UI event that matches the specified criteria to occur.

        For customization of the callback, use keyword args labeled
        'callback', 'args', and 'kwargs' for the callback fn, callback args,
        and callback kwargs, respectively.  Also note that on return,
        the observer-returned UI element will be included in the first
        argument if 'args' are given.  Note also that if the UI element is
        destroyed, callback should not use it, otherwise the function will
        hang.
        """
        return Observer(self).wait_for(
            filter_= match_filter(**kwargs),
            notification=notification,
            timeout=timeout,
        )
