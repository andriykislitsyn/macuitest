from unittest import mock

from macuitest.lib.elements.native_element import NativeElement


def test_value_setter_writes_the_ax_value():
    element = NativeElement(item=mock.Mock())

    element.value = "new"

    element.item.set_ax_attribute.assert_called_once_with("AXValue", "new")
