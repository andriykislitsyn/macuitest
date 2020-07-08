from macuitest.lib.elements.ax11.mixins.match import match_filter


class SearchMethodsMixin:
    def find_first(self, **kwargs):
        """Return the first object that matches the criteria."""
        return self._find_first(**kwargs)

    def find_all(self, **kwargs):
        """Return a list of all children that match the specified criteria."""
        return list(self._find_all(**kwargs))

    def text_areas(self, match=None):
        return self._convenience_match('AXTextArea', 'AXTitle', match)

    def text_areas_r(self, match=None):
        return self._convenience_match('AXTextArea', 'AXTitle', match, recursive=True)

    def text_fields(self, match=None):
        return self._convenience_match('AXTextField', 'AXRoleDescription', match)

    def text_fields_r(self, match=None):
        return self._convenience_match('AXTextField', 'AXRoleDescription', match, recursive=True)

    def buttons(self, match=None):
        return self._convenience_match('AXButton', 'AXTitle', match)

    def buttons_r(self, match=None):
        return self._convenience_match('AXButton', 'AXTitle', match, recursive=True)

    def windows(self, match=None):
        return self._convenience_match('AXWindow', 'AXTitle', match)

    def windows_r(self, match=None):
        return self._convenience_match('AXWindow', 'AXTitle', match, recursive=True)

    def sheets(self, match=None):
        return self._convenience_match('AXSheet', 'AXDescription', match)

    def sheets_r(self, match=None):
        return self._convenience_match('AXSheet', 'AXDescription', match, recursive=True)

    def static_texts(self, match=None):
        return self._convenience_match('AXStaticText', 'AXValue', match)

    def static_texts_r(self, match=None):
        return self._convenience_match('AXStaticText', 'AXValue', match, recursive=True)

    def groups(self, match=None):
        """Return a list of groups with an optional match parameter."""
        return self._convenience_match('AXGroup', 'AXRoleDescription', match)

    def groups_r(self, match=None):
        """Return a list of groups with an optional match parameter."""
        return self._convenience_match('AXGroup', 'AXRoleDescription', match, recursive=True)

    def radio_buttons(self, match=None):
        """Return a list of radio buttons with an optional match parameter."""
        return self._convenience_match('AXRadioButton', 'AXTitle', match)

    def radio_buttons_r(self, match=None):
        """Return a list of radio buttons with an optional match parameter."""
        return self._convenience_match('AXRadioButton', 'AXTitle', match, recursive=True)

    def pop_up_buttons(self, match=None):
        """Return a list of popup menus with an optional match parameter."""
        return self._convenience_match('AXPopUpButton', 'AXTitle', match)

    def pop_up_buttons_r(self, match=None):
        """Return a list of popup menus with an optional match parameter."""
        return self._convenience_match('AXPopUpButton', 'AXTitle', match, recursive=True)

    def rows(self, match=None):
        """Return a list of rows with an optional match parameter."""
        return self._convenience_match('AXRow', 'AXTitle', match)

    def rows_r(self, match=None):
        """Return a list of rows with an optional match parameter."""
        return self._convenience_match('AXRow', 'AXTitle', match, recursive=True)

    def sliders(self, match=None):
        """Return a list of sliders with an optional match parameter."""
        return self._convenience_match('AXSlider', 'AXValue', match)

    def sliders_r(self, match=None):
        """Return a list of sliders with an optional match parameter."""
        return self._convenience_match('AXSlider', 'AXValue', match, recursive=True)

    def menu_items(self, menuitem, *args):
        """Return the specified menu item.

        Example - refer to items by name:

        app._menuItem(app.AXMenuBar, 'File', 'New').Press()
        app._menuItem(app.AXMenuBar, 'Edit', 'Insert', 'Line Break').Press()

        Refer to items by index:

        app._menuitem(app.AXMenuBar, 1, 0).Press()

        Refer to items by mix-n-match:

        app._menuitem(app.AXMenuBar, 1, 'About TextEdit').Press()
        """
        for item in args:
            # If the item has an AXMenu as a child, navigate into it.
            # This seems like a silly abstraction added by apple's a11y api.
            if menuitem.AXChildren[0].AXRole == 'AXMenu':
                menuitem = menuitem.AXChildren[0]
            # Find AXMenuBarItems and AXMenuItems using a handy wildcard
            try:
                menuitem = menuitem.AXChildren[int(item)]
            except ValueError:
                menuitem = menuitem.find_first(AXRole='AXMenu*Item', AXTitle=item)
        return menuitem

    def _convenience_match(self, role, attr, match, recursive=False):
        """Method used by role based convenience functions to find a match"""
        kwargs = dict()
        # If the user supplied some text to search for, supply that in the kwargs.
        if match:
            kwargs[attr] = match
        return self._find_all(AXRole=role, recursive=recursive, **kwargs)

    def _find_all(self, recursive: bool = False, **kwargs):
        """Return a list of all children that match the specified criteria."""
        return list(filter(match_filter(**kwargs), self._generate_children(recursive=recursive), ))

    def _find_first(self, recursive: bool = False, **kwargs):
        """Return the first object that matches the criteria."""
        for item in self._find_all(recursive=recursive, **kwargs):
            return item

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
