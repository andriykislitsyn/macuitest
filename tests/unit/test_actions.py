from unittest import mock

import pytest

from macuitest.config.constants import Point
from macuitest.config.constants import Region
from macuitest.lib import actions
from macuitest.lib.elements import applescript_element as script
from macuitest.lib.elements import native_element as native
from macuitest.lib.elements.controllers.mouse import Mouse
from macuitest.lib.elements.native.calls import AXErrorInvalidUIElement
from macuitest.lib.elements.native.calls import AXErrorUnsupported
from macuitest.lib.elements.visible_text import VisibleText


def ax_item(**attributes):
    """An accessibility element with fixed attributes and a 24x24 frame at (412, 88)."""
    item = mock.Mock()
    values = {"AXPosition": (412, 88), "AXSize": (24, 24), **attributes}
    item.get_ax_attribute.side_effect = values.get
    item.ax_actions = ["AXPress"]
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


def test_press_performs_the_press_action_on_an_element_declared_without_kind():
    item = ax_item()
    actions.press(native.NativeElement(item=item))

    item.press.assert_called_once_with()


def test_press_refuses_an_element_without_a_press_action():
    item = ax_item()
    item.ax_actions = ["AXShowMenu"]

    with pytest.raises(actions.ActionError, match="AXShowMenu"):
        actions.press(native.StaticText(item=item))

    item.press.assert_not_called()


def test_press_clicks_an_applescript_element_with_the_pause():
    element = mock.create_autospec(script.Button, instance=True)

    actions.press(element, pause=0.5)

    element.click.assert_called_once_with(0.5)


def test_press_rejects_a_screen_element_and_suggests_click():
    with pytest.raises(actions.UsageError, match="click"):
        actions.press(mock.create_autospec(VisibleText, instance=True))


def test_set_value_writes_text_to_an_ax_element():
    item = ax_item(AXValue="old")

    actions.set_value(native.TextField(item=item), "new")

    item.set_ax_attribute.assert_called_once_with("AXValue", "new")


def test_set_value_converts_to_the_current_value_type():
    item = ax_item(AXValue=0)

    actions.set_value(native.CheckBox(item=item), "1")

    item.set_ax_attribute.assert_called_once_with("AXValue", 1)


def test_set_value_rejects_a_value_that_isnt_a_number_for_a_number():
    with pytest.raises(ValueError):
        actions.set_value(native.CheckBox(item=ax_item(AXValue=0)), "on")


def test_set_value_raises_the_accessibility_error_when_not_settable():
    item = ax_item(AXValue="old")
    item.set_ax_attribute.side_effect = AXErrorUnsupported('Attribute "AXValue" is not settable')

    with pytest.raises(AXErrorUnsupported):
        actions.set_value(native.TextField(item=item), "new")


def test_set_value_types_into_an_applescript_text_element():
    element = mock.create_autospec(script.TextField, instance=True)

    actions.set_value(element, "hi")

    element.set_text.assert_called_once_with("hi")


def test_set_value_rejects_a_screen_element():
    with pytest.raises(actions.UsageError):
        actions.set_value(mock.create_autospec(VisibleText, instance=True), "x")


@pytest.fixture
def front_app(monkeypatch):
    """Serve an app root that reaches the front once activated."""
    root = mock.Mock()
    root.get_ax_attribute.side_effect = lambda name: name == "AXFrontmost"
    monkeypatch.setattr(actions, "app_root", lambda app: root)
    return root


@pytest.fixture
def mouse(monkeypatch):
    fake = mock.create_autospec(Mouse, instance=True)
    monkeypatch.setattr(actions, "mouse", fake)
    return fake


@pytest.mark.parametrize(
    "options, method",
    [({}, "click"), ({"double": True}, "double_click"), ({"right": True}, "right_click")],
)
def test_click_clicks_the_element_center_once_the_app_is_in_front(
    front_app, mouse, options, method
):
    actions.click(native.Button(item=ax_item()), "TextEdit", **options)

    front_app.activate.assert_called_once_with()
    getattr(mouse, method).assert_called_once_with(424, 100)


def test_click_locates_a_screen_element_after_activating_the_app(front_app, mouse):
    calls = mock.Mock()
    front_app.activate.side_effect = lambda: calls.activate()
    element = mock.create_autospec(VisibleText, instance=True)
    element.get_center.side_effect = lambda: (calls.locate(), Point(5, 6))[1]

    actions.click(element, "TextEdit")

    assert [call[0] for call in calls.mock_calls] == ["activate", "locate"]
    mouse.click.assert_called_once_with(5, 6)


def test_click_refuses_when_the_app_leaves_the_front_while_locating(front_app, mouse):
    front_app.get_ax_attribute.side_effect = [True, False]

    with pytest.raises(actions.FocusError):
        actions.click(native.Button(item=ax_item()), "TextEdit")

    mouse.click.assert_not_called()


def test_click_refuses_an_applescript_element_of_another_process(front_app, mouse):
    element = mock.create_autospec(script.Button, instance=True)
    element.process = "Finder"

    with pytest.raises(actions.UsageError, match="Finder"):
        actions.click(element, "TextEdit")

    front_app.activate.assert_not_called()


def test_click_refuses_when_the_app_doesnt_reach_the_front(monkeypatch, mouse):
    root = mock.Mock()
    root.get_ax_attribute.return_value = False
    monkeypatch.setattr(actions, "app_root", lambda app: root)
    monkeypatch.setattr(actions, "FOCUS_TIMEOUT", 0)
    element = mock.create_autospec(native.Button, instance=True)

    with pytest.raises(actions.FocusError, match="TextEdit"):
        actions.click(element, "TextEdit")

    mouse.click.assert_not_called()


def test_click_raises_lookup_error_when_the_app_has_no_window(monkeypatch):
    monkeypatch.setattr(actions, "app_root", lambda app: None)

    with pytest.raises(LookupError, match="TextEdit"):
        actions.click(mock.create_autospec(native.Button, instance=True), "TextEdit")


def test_click_needs_the_app():
    with pytest.raises(actions.UsageError, match="app"):
        actions.click(mock.create_autospec(native.Button, instance=True), None)


def test_click_rejects_double_and_right_together(front_app):
    with pytest.raises(actions.UsageError):
        actions.click(
            mock.create_autospec(native.Button, instance=True), "TextEdit", double=True, right=True
        )


def test_read_strips_bidi_marks_apps_put_around_text():
    element = native.StaticText(item=ax_item(AXValue="‎7‎"))

    assert actions.read(element) == "7"


def test_read_returns_none_for_a_static_text_without_a_value():
    element = native.StaticText(item=ax_item(AXValue=None))

    assert actions.read(element) is None


def test_find_strips_bidi_marks_from_the_value():
    element = native.StaticText(item=ax_item(AXRole="AXStaticText", AXValue="‎42"))

    snapshot = actions.find(element)

    assert snapshot is not None
    assert snapshot.value == "42"


def test_click_raises_no_window_error_when_the_app_has_no_window(monkeypatch):
    monkeypatch.setattr(actions, "app_root", lambda app: None)

    with pytest.raises(actions.NoWindowError, match="TextEdit has no window"):
        actions.click(mock.create_autospec(native.Button, instance=True), "TextEdit")


def test_bring_to_front_returns_a_check_that_reads_focus_again(front_app):
    front_app.get_ax_attribute.side_effect = [True, False]

    in_front = actions.bring_to_front("TextEdit")

    front_app.activate.assert_called_once_with()
    assert in_front() is False


def test_bring_to_front_raises_no_window_error_without_a_window(monkeypatch):
    monkeypatch.setattr(actions, "app_root", lambda app: None)

    with pytest.raises(actions.NoWindowError, match="TextEdit has no window"):
        actions.bring_to_front("TextEdit")


def test_bring_to_front_reads_an_app_that_quit_as_not_in_front(front_app, monkeypatch):
    monkeypatch.setattr(actions, "FOCUS_TIMEOUT", 0)
    front_app.get_ax_attribute.side_effect = AXErrorInvalidUIElement("gone")

    with pytest.raises(actions.FocusError, match="TextEdit"):
        actions.bring_to_front("TextEdit")
