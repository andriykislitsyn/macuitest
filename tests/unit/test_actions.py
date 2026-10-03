from unittest import mock

import pytest

from macuitest.config.constants import Region
from macuitest.lib import actions
from macuitest.lib.elements import applescript_element as script
from macuitest.lib.elements import native_element as native
from macuitest.lib.elements.visible_text import VisibleText


def ax_item(**attributes):
    """An accessibility element with fixed attributes and a 24x24 frame at (412, 88)."""
    item = mock.Mock()
    values = {"AXPosition": (412, 88), "AXSize": (24, 24), **attributes}
    item.get_ax_attribute.side_effect = values.get
    return item


def test_find_describes_an_ax_element():
    element = native.Button(item=ax_item(AXRole="AXButton", AXTitle="Search", AXValue=None))

    assert actions.find(element) == actions.Snapshot(
        role="AXButton", title="Search", value=None, box=Region(412, 88, 436, 112)
    )


def test_find_returns_none_for_a_missing_ax_element():
    element = native.Button(find=mock.Mock(side_effect=LookupError("gone")))

    assert actions.find(element) is None


def test_find_returns_the_box_of_a_screen_element():
    element = mock.create_autospec(VisibleText, instance=True)
    element.locate.return_value = Region(1, 2, 3, 4)

    assert actions.find(element) == actions.Snapshot(box=Region(1, 2, 3, 4))
    element.locate.assert_called_once_with()


def test_find_returns_none_for_a_screen_element_not_on_screen():
    element = mock.create_autospec(VisibleText, instance=True)
    element.locate.return_value = None

    assert actions.find(element) is None


def test_read_returns_a_text_field_text():
    element = native.TextField(item=ax_item(AXValue="Untitled"))

    assert actions.read(element) == "Untitled"


def test_read_returns_any_other_ax_value():
    element = native.CheckBox(item=ax_item(AXValue=1))

    assert actions.read(element) == 1


def test_read_returns_an_applescript_text_element_text():
    element = mock.create_autospec(script.TextField, instance=True)
    element.get_text.return_value = "42"

    assert actions.read(element) == "42"


def test_read_rejects_a_screen_element():
    with pytest.raises(actions.UsageError, match="ax\\(\\) or applescript\\(\\)"):
        actions.read(mock.create_autospec(VisibleText, instance=True))


@pytest.mark.parametrize("vanish, method", [(False, "wait_displayed"), (True, "wait_vanish")])
def test_wait_passes_the_timeout_to_the_matching_wait(vanish, method):
    element = mock.create_autospec(native.NativeElement, instance=True)
    getattr(element, method).return_value = True

    assert actions.wait(element, vanish=vanish, timeout=3) is True
    getattr(element, method).assert_called_once_with(3)


def test_wait_reads_a_screen_box_as_success():
    element = mock.create_autospec(VisibleText, instance=True)
    element.wait_displayed.return_value = Region(1, 2, 3, 4)

    assert actions.wait(element) is True


def test_wait_reads_a_timeout_as_failure():
    element = mock.create_autospec(VisibleText, instance=True)
    element.wait_displayed.return_value = None

    assert actions.wait(element) is False


def test_find_describes_an_applescript_element_by_its_value():
    element = mock.create_autospec(script.Button, instance=True)
    type(element).exists = mock.PropertyMock(return_value=True)
    type(element).value = mock.PropertyMock(return_value="OK")

    assert actions.find(element) == actions.Snapshot(value="OK")


def test_find_returns_none_for_a_missing_applescript_element():
    element = mock.create_autospec(script.Button, instance=True)
    type(element).exists = mock.PropertyMock(return_value=False)

    assert actions.find(element) is None
