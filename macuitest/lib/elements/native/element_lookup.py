import fnmatch
from typing import Optional


class LookUpMixin:
    def find_element(self, **kwargs):
        """Return the first object that matches the criteria."""
        return self._find_element(**kwargs)

    def find_elements(self, **kwargs):
        """Return a list of all children that match the specified criteria."""
        return list(self._find_elements(**kwargs))

    def text_areas(self, title: Optional[str] = None):
        return self._convenience_match('AXTextArea', 'AXTitle', title)

    def text_areas_r(self, title: Optional[str] = None):
        return self._convenience_match('AXTextArea', 'AXTitle', title, recursive=True)

    def text_fields(self, role_description: Optional[str] = None):
        return self._convenience_match('AXTextField', 'AXRoleDescription', role_description)

    def text_fields_r(self, role_description: Optional[str] = None):
        return self._convenience_match('AXTextField', 'AXRoleDescription', role_description, recursive=True)

    def buttons(self, title: Optional[str] = None):
        return self._convenience_match('AXButton', 'AXTitle', title)

    def buttons_r(self, title: Optional[str] = None):
        return self._convenience_match('AXButton', 'AXTitle', title, recursive=True)

    def windows(self, title: Optional[str] = None):
        return self._convenience_match('AXWindow', 'AXTitle', title)

    def windows_r(self, title: Optional[str] = None):
        return self._convenience_match('AXWindow', 'AXTitle', title, recursive=True)

    def sheets(self, role_description: Optional[str] = None):
        return self._convenience_match('AXSheet', 'AXDescription', role_description)

    def sheets_r(self, role_description: Optional[str] = None):
        return self._convenience_match('AXSheet', 'AXDescription', role_description, recursive=True)

    def static_texts(self, value: Optional[str] = None):
        return self._convenience_match('AXStaticText', 'AXValue', value)

    def static_texts_r(self, value: Optional[str] = None):
        return self._convenience_match('AXStaticText', 'AXValue', value, recursive=True)

    def groups(self, role_description: Optional[str] = None):
        """Return a list of groups with an optional match parameter."""
        return self._convenience_match('AXGroup', 'AXRoleDescription', role_description)

    def groups_r(self, role_description: Optional[str] = None):
        """Return a list of groups with an optional match parameter."""
        return self._convenience_match('AXGroup', 'AXRoleDescription', role_description, recursive=True)

    def radio_buttons(self, title: Optional[str] = None):
        """Return a list of radio buttons with an optional match parameter."""
        return self._convenience_match('AXRadioButton', 'AXTitle', title)

    def radio_buttons_r(self, title: Optional[str] = None):
        """Return a list of radio buttons with an optional match parameter."""
        return self._convenience_match('AXRadioButton', 'AXTitle', title, recursive=True)

    def pop_up_buttons(self, title: Optional[str] = None):
        """Return a list of popup menus with an optional match parameter."""
        return self._convenience_match('AXPopUpButton', 'AXTitle', title)

    def pop_up_buttons_r(self, title: Optional[str] = None):
        """Return a list of popup menus with an optional match parameter."""
        return self._convenience_match('AXPopUpButton', 'AXTitle', title, recursive=True)

    def rows(self, title: Optional[str] = None):
        """Return a list of rows with an optional match parameter."""
        return self._convenience_match('AXRow', 'AXTitle', title)

    def rows_r(self, title: Optional[str] = None):
        """Return a list of rows with an optional match parameter."""
        return self._convenience_match('AXRow', 'AXTitle', title, recursive=True)

    def sliders(self, value: Optional[str] = None):
        """Return a list of sliders with an optional match parameter."""
        return self._convenience_match('AXSlider', 'AXValue', value)

    def sliders_r(self, value: Optional[str] = None):
        """Return a list of sliders with an optional match parameter."""
        return self._convenience_match('AXSlider', 'AXValue', value, recursive=True)

    @staticmethod
    def menu_items(menuitem, *args):
        """ Return the specified menu item.
            Refer to items by name:
                app._menuItem(app.AXMenuBar, 'File', 'New').Press()
                app._menuItem(app.AXMenuBar, 'Edit', 'Insert', 'Line Break').Press()
            Refer to items by index:
                app._menuitem(app.AXMenuBar, 1, 0).Press()
            Refer to items by mix-n-match:
                app._menuitem(app.AXMenuBar, 1, 'About TextEdit').Press()
        """
        for item in args:
            if menuitem.AXChildren[0].AXRole == 'AXMenu':  # If the item has an AXMenu as a child, navigate into it.
                menuitem = menuitem.AXChildren[0]
            try:
                menuitem = menuitem.AXChildren[int(item)]  # Find AXMenuBarItems and AXMenuItems using a handy wildcard.
            except ValueError:
                menuitem = menuitem.find_first(AXRole='AXMenu*Item', AXTitle=item)
        return menuitem

    def _convenience_match(self, role, attr, match, recursive=False):
        """Method used by role based convenience functions to find a match."""
        kwargs = dict()
        if match:  # If the user supplied some text to search for, supply that in the kwargs.
            kwargs[attr] = match
        return self._find_elements(AXRole=role, recursive=recursive, **kwargs)

    def _find_element(self, recursive: bool = False, **kwargs):
        """Return the first object that matches the criteria."""
        for item in self._find_elements(recursive=recursive, **kwargs):
            return item

    def _find_elements(self, recursive: bool = False, **kwargs):
        """Return a list of all children that match the specified criteria."""
        return list(filter(match_filter(**kwargs), self._generate_children(recursive=recursive), ))

    def _generate_children(self, target=None, recursive=False):
        """Generator which yields all AXChildren of the object."""
        if target is None:
            target = self

        if 'AXChildren' not in target.ax_attributes:
            return

        for child in target.AXChildren:
            yield child
            if recursive:
                for c in self._generate_children(child, recursive):
                    yield c


def match_filter(**kwargs):
    def _match(obj):
        for k in kwargs.keys():
            try:
                val = getattr(obj, k)
            except AttributeError:
                return False
            if isinstance(val, str):
                if not fnmatch.fnmatch(val, kwargs[k]):
                    return False
            else:
                if val != kwargs[k]:
                    return False
        return True

    return _match
