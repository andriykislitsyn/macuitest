from unittest import mock

import pytest

from macuitest.config.settings import settings
from macuitest.lib.elements import native_element
from macuitest.lib.elements.native_element import NativeElement


def test_value_setter_writes_the_ax_value():
    element = NativeElement(item=mock.Mock())

    element.value = "new"

    element.item.set_ax_attribute.assert_called_once_with("AXValue", "new")


FRAME = {"AXPosition": (10, 20), "AXSize": (100, 40), "AXRole": "AXButton"}


def appearing(after):
    """Return a `find` that raises `LookupError` `after` times, then finds an element."""
    calls = []

    def find():
        calls.append(None)
        if len(calls) <= after:
            raise LookupError("not yet")
        return mock.Mock(get_ax_attribute=FRAME.get)

    return find


@pytest.fixture
def mouse():
    with mock.patch.object(native_element, "mouse") as fake:
        yield fake


@pytest.mark.parametrize(
    "method, controller, options",
    [
        ("click_mouse", "click", {"hold": 1, "duration": 2, "pause": 3}),
        ("right_click_mouse", "right_click", {"hold": 1, "duration": 2, "pause": 3}),
        ("double_click_mouse", "double_click", {"duration": 2}),
        ("hover_mouse", "hover", {"duration": 2}),
    ],
)
def test_mouse_methods_pass_their_options(mouse, method, controller, options):
    element = NativeElement(item=mock.Mock(get_ax_attribute=FRAME.get))

    getattr(element, method)(1, 1, **options)

    getattr(mouse, controller).assert_called_once_with(61, 41, **options)


@pytest.mark.parametrize(
    "method", ["click_mouse", "right_click_mouse", "double_click_mouse", "hover_mouse"]
)
def test_mouse_options_are_keyword_only(mouse, method):
    element = NativeElement(item=mock.Mock(get_ax_attribute=FRAME.get))

    with pytest.raises(TypeError):
        getattr(element, method)(0, 0, 0.5)


def test_is_visible_checks_once_without_waiting():
    find = mock.Mock(side_effect=LookupError("gone"))

    assert NativeElement(find=find).is_visible is False
    assert find.call_count == 1


def test_wait_displayed_waits_for_a_late_element():
    assert NativeElement(find=appearing(after=2)).wait_displayed(timeout=1) is True


def test_wait_displayed_gives_up_after_the_timeout():
    find = mock.Mock(side_effect=LookupError("gone"))

    assert NativeElement(find=find).wait_displayed(timeout=0) is False


@pytest.mark.parametrize(
    "method, setting", [("wait_displayed", "timeout"), ("wait_vanish", "vanish_timeout")]
)
def test_waits_default_to_the_elements_timeouts(monkeypatch, method, setting):
    monkeypatch.setattr(settings.elements, setting, 7)
    element = NativeElement(item=mock.Mock(get_ax_attribute=FRAME.get))
    with mock.patch.object(native_element, "wait_condition", autospec=True) as wait:
        getattr(element, method)()

    assert wait.call_args.kwargs["timeout"] == 7
