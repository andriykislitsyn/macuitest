from unittest import mock

import pytest

from macuitest.lib.elements import native_element
from macuitest.lib.elements.native_element import NativeElement


def test_value_setter_writes_the_ax_value():
    element = NativeElement(item=mock.Mock())

    element.value = "new"

    element.item.set_ax_attribute.assert_called_once_with("AXValue", "new")


@pytest.mark.parametrize("method", ["double_click_mouse", "rightclick_mouse"])
def test_mouse_actions_pass_duration_as_duration(method):
    attributes = {"AXPosition": (10, 20), "AXSize": (100, 40)}
    element = NativeElement(item=mock.Mock(get_ax_attribute=attributes.get))
    with mock.patch.object(native_element, "mouse") as mouse:
        getattr(element, method)(duration=0.5)

    mouse_method = getattr(mouse, method.replace("_mouse", "").replace("rightclick", "right_click"))
    mouse_method.assert_called_once_with(60, 40, duration=0.5)
